# SHOW / PLAYLIST DOWNLOADER
# Playlists -> Shows/
#
# Structure:
#
# Shows/
#   Playlist Name/
#       Season 01/
#           S01E001 - Episode.mp4
import json

from yt_dlp import YoutubeDL

URL = "https://www.youtube.com/playlist?list=PL8tvmhX3nfjhypT5JNZlHEfFgZd6_El3-"

opts = {
    # Output structure
    "outtmpl": (
        "downloads/Shows/"
        "%(playlist)s/"
        "Season 01/"
        "S01E%(playlist_index)03d - %(title)s.%(ext)s"
    ),
    # Resume interrupted downloads
    "continuedl": True,
    # Skip already-downloaded videos
    "download_archive": "cache/show_archive.txt",
    # Best quality
    "format": "bestvideo+bestaudio/best",
    # Parallel fragments
    "concurrent_fragment_downloads": 4,
    # Download subtitles
    "writesubtitles": True,
    # Download auto-generated subtitles too
    "writeautomaticsub": True,
    # Subtitle languages
    "subtitleslangs": ["en"],
    # Subtitle format
    "subtitlesformat": "vtt",
    # DO NOT EMBED
    "embedsubtitles": False,
    # Merge format
    "merge_output_format": "mp4",
    "remote-components": "ejs:npm"
}


def progress(d):
    if d["status"] == "downloading":
        print(
            f"[SHOW] "
            f"{d.get('_percent_str')} "
            f"{d.get('_speed_str')} "
            f"ETA: {d.get('_eta_str')}"
        )

    elif d["status"] == "finished":
        print(f"[SHOW] Finished: {d['filename']}")


opts["progress_hooks"] = [progress]

with YoutubeDL(opts) as ydl:
    info = ydl.extract_info(URL, download=False)

    print("Playlist:", info.get("title"))
    print("Uploader:", info.get("uploader"))

    for entry in info["entries"]:
        print(
            entry.get("playlist_index"),
            entry.get("title"),
            entry.get("filesize_approx"),
            entry.get("filesize_approx")
        )
    ydl.download([URL])