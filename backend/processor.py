import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

import requests
from yt_dlp import YoutubeDL
from db_helper import get_all_processes, get_process, get_video, create_video, set_process_finished, create_movie, \
    create_show
import json

from paths import cache

# ---------------------------------------------------------------------------
# yt-dlp option presets
# ---------------------------------------------------------------------------

thumb_opts = {
    "continuedl": True,
    "format": "bestvideo+bestaudio/best",
    "concurrent_fragment_downloads": 4,
    "merge_output_format": "mkv",
    "remote-components": "ejs:npm",
}

# ---------------------------------------------------------------------------
# Module-level state shared via _shared_dict
# ---------------------------------------------------------------------------

processes = []
current_process: str = ""
current_video_progress: float = 0.0
current_process_progress: float = 0.0
current_video_progress_details = None
current_process_video_count: int = 0
process_start_time: float = 0.0
process_eta: float = 0.0
current_video_id: str = ""
_shared_dict = None
_videos_remaining: int = 0
_video_download_start: float = 0.0
_total_download_time: float = 0.0
_completed_downloads: int = 0

# How long (seconds) to sleep between polls when the queue is empty
_POLL_INTERVAL: float = 10.0


# ---------------------------------------------------------------------------
# Shared-dict sync helpers
# ---------------------------------------------------------------------------

def _sync() -> None:
    """Push all progress globals into the shared dict."""
    if _shared_dict is None:
        return
    _shared_dict["current_process"] = current_process
    _shared_dict["current_video_progress"] = current_video_progress
    _shared_dict["current_process_progress"] = current_process_progress
    _shared_dict["current_process_video_count"] = current_process_video_count
    _shared_dict["process_eta"] = process_eta
    _shared_dict["current_video_id"] = current_video_id


def _update_progress(completed: int, total: int) -> None:
    """Set current_process_progress (0–100 %). ETA is handled by the progress hook."""
    global current_process_progress
    current_process_progress = (completed / total) * 100.0 if total else 0.0
    _sync()


# ---------------------------------------------------------------------------
# yt-dlp progress hook
# ---------------------------------------------------------------------------

def progress(d):
    global current_video_progress, process_eta
    if d["status"] != "downloading":
        return
    if d.get("info_dict", {}).get("vcodec") == "none":
        return
    current_video_progress = d["_percent"]
    ytdlp_eta = d.get("eta") or 0.0
    avg = (
        _total_download_time / _completed_downloads
        if _completed_downloads > 0
        else float(ytdlp_eta)
    )
    process_eta = ytdlp_eta + avg * _videos_remaining
    _sync()


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def _copy_existing_video(video_id: str, dst: Path) -> bool:
    """
    Look up an already-downloaded video in the DB and copy it to *dst*.
    Returns True if a usable source file was found and copied, False otherwise.
    """
    existing = get_video(video_id)
    if not existing:
        return False
    src = Path(existing.path)
    if not src.exists():
        print(f"DB record found for {video_id} but file missing at {src}, will redownload.")
        return False
    if src.resolve() == dst.resolve():
        print(f"Source and destination are the same for {video_id}, skipping copy.")
        return True
    dst.parent.mkdir(exist_ok=True, parents=True)
    shutil.copy2(src, dst)
    print(f"Copied existing file: {src} → {dst}")
    return True


def _download_thumbnail(url: str, dst: Path) -> bool:
    """Download a JPEG thumbnail to *dst*. Returns True on success."""
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        dst.parent.mkdir(exist_ok=True, parents=True)
        with open(dst, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        print(f"Thumbnail download failed ({url}): {e}")
        return False


def _convert_thumbnail(src: Path, dst: Path) -> bool:
    """
    Use ffmpeg to convert/resize *src* to a proper JPEG at *dst*.
    Jellyfin is picky about WebP or oddly-encoded JPEGs — ffmpeg normalises them.
    Returns True on success.
    """
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(src),
                "-vf", "scale='min(1280,iw)':-2",   # cap width at 1280 px, keep AR
                "-q:v", "3",                          # JPEG quality (2=best … 31=worst)
                str(dst),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg thumbnail conversion failed: {e}")
        return False


def _pretty_xml(root: ET.Element) -> str:
    """Return a pretty-printed XML string with an XML declaration."""
    raw = ET.tostring(root, encoding="unicode")
    reparsed = minidom.parseString(raw)
    return reparsed.toprettyxml(indent="  ", encoding=None)


# ---------------------------------------------------------------------------
# Jellyfin NFO writers
# ---------------------------------------------------------------------------

def _write_show_nfo(playlist_info: dict, show_dir: Path) -> None:
    """
    Write tvshow.nfo, poster.jpg, fanart.jpg, and banner.jpg for a playlist
    into *show_dir* (= Shows/<playlist title>/).

    NFO schema: https://kodi.wiki/view/NFO_files/TV_shows
    """
    nfo_path = show_dir / "tvshow.nfo"
    if nfo_path.exists():
        print(f"tvshow.nfo already exists, skipping: {nfo_path}")
        return

    root = ET.Element("tvshow")

    def _t(tag: str, text: str | None) -> None:
        if text:
            el = ET.SubElement(root, tag)
            el.text = str(text)

    _t("title",          playlist_info.get("title"))
    _t("originaltitle",  playlist_info.get("title"))
    _t("showtitle",      playlist_info.get("title"))
    _t("plot",           playlist_info.get("description"))
    _t("season",         "1")
    _t("episode",        str(len(playlist_info.get("entries", []))))
    _t("year",           str(playlist_info.get("upload_date", "")[:4]) if playlist_info.get("upload_date") else None)
    _t("id",             playlist_info.get("id"))
    _t("uniqueid",       playlist_info.get("id"))

    # Channel / uploader info
    _t("studio",         playlist_info.get("uploader") or playlist_info.get("channel"))
    _t("channel",        playlist_info.get("channel"))
    _t("channelid",      playlist_info.get("channel_id"))

    # Tags / genres
    for tag in (playlist_info.get("tags") or []):
        _t("tag", tag)
        _t("genre", tag)

    # Webpage link
    _t("webpage_url", playlist_info.get("webpage_url"))

    show_dir.mkdir(exist_ok=True, parents=True)
    nfo_path.write_text(_pretty_xml(root), encoding="utf-8")
    print(f"Wrote {nfo_path}")

    # ---- Show-level artwork ------------------------------------------------
    # Prefer maxresdefault thumbnails; fall back to whatever yt-dlp gives us.
    thumb_url = playlist_info.get("thumbnail") or playlist_info.get("thumbnails", [{}])[-1].get("url", "")

    raw_thumb = show_dir / "_poster_raw.jpg"
    if thumb_url and _download_thumbnail(thumb_url, raw_thumb):
        for art_name in ("poster.jpg", "fanart.jpg", "banner.jpg"):
            art_path = show_dir / art_name
            if not art_path.exists():
                _convert_thumbnail(raw_thumb, art_path)
                print(f"Wrote {art_path}")
        raw_thumb.unlink(missing_ok=True)


def _write_episode_nfo(
    video_info: dict,
    ep_index: int,
    show_dir: Path,
    episode_prefix: str,
    filename_stem: str | None = None,
) -> None:
    """
    Write <episode_prefix> - <name>.nfo and <episode_prefix> - <name>-thumb.jpg
    into *show_dir*/Season 01/.

    *filename_stem*, when provided, should be the actual on-disk stem of the
    downloaded video file (i.e. Path(actual_video_file).stem, with the
    episode prefix stripped if present). This keeps the NFO/thumb filenames
    in sync with whatever yt-dlp actually wrote, since yt-dlp may sanitize
    characters in the title (e.g. '|' → '｜') when saving the video file.
    Falls back to the raw title if not given.

    NFO schema: https://kodi.wiki/view/NFO_files/Episodes
    """
    title = video_info.get("title", f"Episode {ep_index}")
    season_dir = show_dir / "Season 01"
    season_dir.mkdir(exist_ok=True, parents=True)

    safe_title = filename_stem if filename_stem else title
    nfo_path  = season_dir / f"{episode_prefix} - {safe_title}.nfo"
    thumb_path = season_dir / f"{episode_prefix} - {safe_title}-thumb.jpg"

    # ---- NFO ---------------------------------------------------------------
    if not nfo_path.exists():
        root = ET.Element("episodedetails")

        def _t(tag: str, text) -> None:
            if text is not None and str(text).strip():
                el = ET.SubElement(root, tag)
                el.text = str(text)

        _t("title",         title)
        _t("showtitle",     video_info.get("playlist_title") or video_info.get("playlist"))
        _t("season",        "1")
        _t("episode",       str(ep_index + 1))  # 1-based for display
        _t("plot",          video_info.get("description"))
        _t("runtime",       str(round((video_info.get("duration") or 0) / 60)))
        _t("year",          (video_info.get("upload_date") or "")[:4] or None)
        _t("aired",         _fmt_date(video_info.get("upload_date")))
        _t("id",            video_info.get("id"))
        _t("uniqueid",      video_info.get("id"))
        _t("webpage_url",   video_info.get("webpage_url"))

        # View / like counts
        _t("views",         video_info.get("view_count"))
        _t("likes",         video_info.get("like_count"))

        # Uploader as director / studio
        uploader = video_info.get("uploader") or video_info.get("channel")
        if uploader:
            _t("director",  uploader)
            _t("studio",    uploader)

        # Tags
        for tag in (video_info.get("tags") or []):
            _t("tag", tag)

        # Chapters as a simple list in plot_extra
        chapters = video_info.get("chapters") or []
        if chapters:
            chapter_lines = "\n".join(
                f"  {_fmt_seconds(ch['start_time'])}  {ch['title']}"
                for ch in chapters
            )
            _t("chapter_list", chapter_lines)

        nfo_path.write_text(_pretty_xml(root), encoding="utf-8")
        print(f"Wrote {nfo_path}")

    # ---- Episode thumbnail --------------------------------------------------
    if not thumb_path.exists():
        # Try to get the best-quality thumbnail
        thumbnails = video_info.get("thumbnails") or []
        thumb_url = (
            next((t["url"] for t in reversed(thumbnails) if t.get("url")), None)
            or video_info.get("thumbnail")
        )
        if thumb_url:
            raw = thumb_path.with_suffix(".raw.jpg")
            if _download_thumbnail(thumb_url, raw):
                _convert_thumbnail(raw, thumb_path)
                raw.unlink(missing_ok=True)
                print(f"Wrote {thumb_path}")


# ---------------------------------------------------------------------------
# Small formatting helpers
# ---------------------------------------------------------------------------

def _fmt_date(yyyymmdd: str | None) -> str | None:
    """'20231225' → '2023-12-25'  (Jellyfin wants ISO 8601)."""
    if not yyyymmdd or len(yyyymmdd) < 8:
        return None
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"


def _fmt_seconds(seconds: float | int) -> str:
    """Float seconds → 'H:MM:SS'."""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}"


# ---------------------------------------------------------------------------
# Core process handler
# ---------------------------------------------------------------------------

def process_item(process_id: str):
    global current_process_progress
    global current_video_progress
    global current_process
    global current_process_video_count
    global process_start_time
    global current_video_id
    global _videos_remaining, _video_download_start, _total_download_time, _completed_downloads

    current_process_progress = 0.0
    current_video_progress = 0.0
    current_video_id = ""
    current_process = process_id
    process_start_time = time.time()
    _videos_remaining = 0
    _video_download_start = 0.0
    _total_download_time = 0.0
    _completed_downloads = 0

    print(f"Processing {process_id}")
    process = get_process(process_id)
    if not process:
        print("Process not found")
        return

    # -----------------------------------------------------------------------
    # Video process
    # -----------------------------------------------------------------------
    if process.type == "video":
        print("Downloading videos")
        videos = json.loads(process.videos)
        print(f"Found {len(videos)} videos")
        total = len(videos)
        current_process_video_count = total
        videos_completed = 0
        videos_to_process = []
        videos_to_copy = []
        _sync()

        Path("Videos").mkdir(exist_ok=True, parents=True)

        for vid in videos:
            if get_video(vid):
                existing = get_video(vid)
                src = Path(existing.path)
                dst = Path(f"Videos/{src.name}")
                if src.exists() and src.resolve() != dst.resolve():
                    videos_to_copy.append((vid, dst))
                else:
                    print(f"Video already in place: {vid}")
                    videos_completed += 1
                    _update_progress(videos_completed, total)
            else:
                videos_to_process.append(vid)

        for video_id, dst in videos_to_copy:
            print(f"Copying existing video {video_id} to {dst}")
            _copy_existing_video(video_id, dst)
            try:
                create_video(video_id, str(dst))
                create_movie(video_id)
            except Exception as e:
                print(e)
            videos_completed += 1
            _update_progress(videos_completed, total)

        print(videos_to_process)

        # Download thumbnails first
        for video_id in videos_to_process:
            thumb_path = Path(cache / f"videos/{video_id}/thumbnail.jpg")
            if not thumb_path.exists():
                with YoutubeDL(thumb_opts) as ydl:
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    print(url)
                    info = ydl.extract_info(url, download=False)
                r = requests.get(info.get("thumbnail"), stream=True)
                r.raise_for_status()
                vid_path = Path(cache / f"videos/{video_id}/")
                if not vid_path.exists():
                    vid_path.mkdir(exist_ok=True, parents=True)
                with open(vid_path / "thumbnail.jpg", "wb") as f:
                    f.write(r.content)
                print(f"Downloaded thumbnail: {vid_path}")

        # Now download the videos
        for video_id in videos_to_process:
            opts = {
                "outtmpl": "cache/videos/%(id)s/%(title)s.%(ext)s",
                "continuedl": True,
                "format": "bestvideo+bestaudio/best",
                "concurrent_fragment_downloads": 4,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["en"],
                "subtitlesformat": "vtt",
                "embedsubtitles": False,
                "merge_output_format": "mp4",
                "remote-components": "ejs:npm",
            }

            opts["progress_hooks"] = [progress]
            current_video_progress = 0.0
            current_video_id = video_id
            _videos_remaining = total - videos_completed - 1
            _video_download_start = time.time()
            Path(cache / "videos" / video_id).mkdir(exist_ok=True, parents=True)
            url = f"https://www.youtube.com/watch?v={video_id}"
            _sync()

            with YoutubeDL(opts) as ydl:
                ydl.download([url])

            _total_download_time += time.time() - _video_download_start
            _completed_downloads += 1
            videos_completed += 1
            _update_progress(videos_completed, total)

            # Don't reconstruct the filename from the title — yt-dlp may
            # sanitize characters when it writes the file (e.g. '|' → '｜'),
            # so just look at what's actually in the download directory.
            candidates = list(Path(cache / "videos" / video_id).glob("*.mp4"))
            if not candidates:
                print(f"ERROR: no mp4 found in cache dir for {video_id}, skipping move")
                continue
            src = candidates[0]

            dst = Path(f"Videos/{src.name}")

            shutil.move(src, dst)
            print(f"Moved {src} to {dst}")

            try:
                create_video(video_id, str(dst))
                create_movie(video_id)
            except Exception as e:
                print(e)

            for i in Path(cache / "videos" / video_id).glob("*.vtt"):
                vtt_dst = Path(f"Videos/{i.name}")
                shutil.move(i, vtt_dst)
                print(f"Moved {i} to {vtt_dst}")

    # -----------------------------------------------------------------------
    # Playlist process
    # -----------------------------------------------------------------------
    elif process.type == "playlist":
        print("Downloading playlist")
        opts3 = {
            "continuedl": True,
            "format": "bestvideo+bestaudio/best",
            "concurrent_fragment_downloads": 4,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "subtitlesformat": "vtt",
            "embedsubtitles": False,
            "merge_output_format": "mp4",
            "remote-components": "ejs:npm",
        }
        with YoutubeDL(opts3) as ydl:
            URL = f"https://www.youtube.com/playlist?list={process.playlist}"
            playlist_info = ydl.extract_info(URL, download=False)

        videos = playlist_info["entries"]
        print(f"Found {len(videos)} videos")
        total = len(videos)
        current_process_video_count = total
        playlist_title = playlist_info["title"]
        videos_to_process = [v["id"] for v in videos]
        videos_completed = 0
        _sync()

        print(videos_to_process)

        # Jellyfin show directory tree (final destination)
        show_dir = Path(f"Shows/{playlist_title}")
        show_final_season_dir = show_dir / "Season 01"
        show_dir.mkdir(exist_ok=True, parents=True)
        show_final_season_dir.mkdir(exist_ok=True, parents=True)

        # Staging (cache) directory tree — videos, subtitles, NFOs, and
        # artwork are all downloaded/written here first. Only once a given
        # set of files is fully ready does it get moved into show_dir.
        show_staging_dir = Path(f"cache/{process_id}/{playlist_title}")
        show_staging_season_dir = show_staging_dir / "Season 01"
        show_staging_season_dir.mkdir(exist_ok=True, parents=True)

        # Write show-level NFO + artwork into the cache first, then move the
        # finished files into their final location.
        _write_show_nfo(playlist_info, show_staging_dir)
        for item in show_staging_dir.iterdir():
            if item.is_file():
                target = show_dir / item.name
                shutil.move(str(item), str(target))
                print(f"Moved {item} → {target}")

        # Download thumbnails first (cached for later NFO use)
        video_infos: dict[str, dict] = {}   # video_id → full yt-dlp info dict
        for video_id in videos_to_process:
            thumb_path = Path(cache / f"videos/{video_id}/thumbnail.jpg")
            vid_cache_dir = Path(cache / "videos" / video_id)
            vid_cache_dir.mkdir(exist_ok=True, parents=True)
            if not thumb_path.exists():
                with YoutubeDL(thumb_opts) as ydl:
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    print(url)
                    vinfo = ydl.extract_info(url, download=False)
                video_infos[video_id] = vinfo
                _download_thumbnail(vinfo.get("thumbnail", ""), thumb_path)
                print(f"Downloaded thumbnail: {thumb_path}")
            else:
                # Still need the info dict for NFO writing
                with YoutubeDL(thumb_opts) as ydl:
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    vinfo = ydl.extract_info(url, download=False)
                video_infos[video_id] = vinfo

        vid_index = -1
        # Now download, write NFOs, and write episode thumbnails
        for video_id in videos_to_process:
            vid_index += 1
            episode_prefix = f"S01E{vid_index:02d}"

            opts = {
                "outtmpl": (
                    f"cache/{current_process}/"
                    f"{playlist_title}/"
                    "Season 01/"
                    f"{episode_prefix} - %(title)s.%(ext)s"
                ),
                "continuedl": True,
                "format": "bestvideo+bestaudio/best",
                "concurrent_fragment_downloads": 4,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["en"],
                "subtitlesformat": "vtt",
                "embedsubtitles": False,
                "merge_output_format": "mp4",
                "remote-components": "ejs:npm",
            }

            opts["progress_hooks"] = [progress]
            current_video_progress = 0.0
            current_video_id = video_id
            _videos_remaining = total - videos_completed - 1
            _video_download_start = time.time()
            Path(cache / "videos" / video_id).mkdir(exist_ok=True, parents=True)
            url = f"https://www.youtube.com/watch?v={video_id}"
            _sync()

            with YoutubeDL(opts) as ydl:
                ydl.download([url])
            vinfo = video_infos.get(video_id, {})

            _total_download_time += time.time() - _video_download_start
            _completed_downloads += 1
            videos_completed += 1
            _update_progress(videos_completed, total)

            # Don't reconstruct the filename from the title — yt-dlp may
            # sanitize characters when it writes the file (e.g. '|' → '｜'),
            # so just look at what's actually in the staging directory for
            # this episode.
            candidates = list(show_staging_season_dir.glob(f"{episode_prefix} - *.mp4"))
            if not candidates:
                print(f"ERROR: no mp4 found in staging dir for {video_id} ({episode_prefix}), skipping")
                continue
            actual_path = candidates[0]

            # Strip the episode prefix off the real filename to get a stem
            # that matches what yt-dlp actually wrote, for use in NFO/thumb
            # filenames so they stay in sync with the video file.
            stem = actual_path.stem
            prefix_marker = f"{episode_prefix} - "
            if stem.startswith(prefix_marker):
                filename_stem = stem[len(prefix_marker):]
            else:
                filename_stem = stem

            # Write episode NFO + thumbnail into the staging dir, right next
            # to the freshly-downloaded video, using the real on-disk
            # filename stem so NFO/thumb names match the video file exactly.
            _write_episode_nfo(vinfo, vid_index, show_staging_dir, episode_prefix, filename_stem=filename_stem)

            # The video, subtitles, NFO, and thumbnail for this episode are
            # now all sitting in the staging dir — move the whole set into
            # the final show directory together, right now, instead of
            # waiting for the rest of the playlist to finish downloading.
            for f in show_staging_season_dir.glob(f"{episode_prefix} - *"):
                target = show_final_season_dir / f.name
                shutil.move(str(f), str(target))
                print(f"Moved {f} → {target}")

            final_path = show_final_season_dir / actual_path.name
            try:
                create_video(video_id, str(final_path))
            except Exception as e:
                print(e)

        create_show(process.playlist, videos_to_process)
        # Clean up the now-empty staging directory for this playlist.
        shutil.rmtree(show_staging_dir, ignore_errors=True)

    set_process_finished(current_process)


# ---------------------------------------------------------------------------
# Entry point — poll loop
# ---------------------------------------------------------------------------

def start(shared_dict):
    global current_process
    global _shared_dict

    _shared_dict = shared_dict
    _sync()

    # Track which process IDs we have already seen so we never re-run them.
    seen_ids: set[str] = set()

    print("Processor started — scanning for unfinished processes.")
    while True:
        all_procs = get_all_processes()
        unfinished = [p for p in all_procs if not p.finished and p.id not in seen_ids]

        if unfinished:
            for p in unfinished:
                seen_ids.add(p.id)
                processes.append(p)
                current_process = p.id
                print(f"Selected process: {current_process}")
                process_item(current_process)
        else:
            print(f"No new processes — sleeping {_POLL_INTERVAL}s …")
            time.sleep(_POLL_INTERVAL)