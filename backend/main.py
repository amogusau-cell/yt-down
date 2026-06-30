import io
import json
import os
import uuid
import bcrypt
import requests
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from yt_dlp import YoutubeDL

from db_helper import (check_user_password, create_user, get_user_by_username,
                       delete_user, create_user_hashed_password, get_all_users,
                       get_all_processes, create_process, delete_process,
                       get_process, get_video, get_all_videos)
from token_helper import verify_token, verify_admin_token, create_user_token
from pathlib import Path
from paths import config, cache
from fastapi.responses import StreamingResponse, FileResponse
from processor import start
from multiprocessing import Process, Manager
from contextlib import asynccontextmanager


opts = {
    # Output structure
    "outtmpl": (
        "Shows/"
        "%(playlist)s/"
        "Season 01/"
        "S01E%(playlist_index)03d - %(title)s.%(ext)s"
    ),
    # Resume interrupted downloads
    "continuedl": True,
    # Best quality
    "format": "bestvideo+bestaudio/best",
    # Parallel fragments
    "concurrent_fragment_downloads": 4,
    # Merge format
    "merge_output_format": "mkv",
    "remote-components": "ejs:npm"
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    manager = Manager()
    shared = manager.dict()

    proc = Process(target=start, args=(shared,))
    proc.start()
    app.state.shared = shared

    yield

    proc.terminate()
    proc.join()
    manager.shutdown()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, data: dict):
        for ws in self.active:
            await ws.send_json(data)

manager = ConnectionManager()

@app.get("/")
def root_api():
    return {"message": "Hello World"}


@app.post("/login")
def login_api(username: str = Form(...), password: str = Form(...)):
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username or password is required")
    usr = get_user_by_username(username)
    if not usr:
        raise HTTPException(status_code=404, detail="User not found")

    if not check_user_password(username, password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return create_user_token(username, password, usr.role)


@app.post("/register")
def register_api(username: str = Form(...), password: str = Form(...)):
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username or password is required")
    create_user(username, password, "usr")
    return "User created successfully"


@app.post("/register/admin")
def register_admin_api(username: str = Form(...), password: str = Form(...)):
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username or password is required")
    usr = get_user_by_username(username)
    if usr:
        raise HTTPException(status_code=409, detail="Username already exists")
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt)
    data = {"username": username, "password": password_hash.decode("utf-8"), "can_create": False}
    with open(cache / f"admin/admin-create-{username}.json", "w") as f:
        json.dump(data, f, indent=2)
    return "Allow admin from server file"


@app.post("/register/admin/checked")
def registered_admin_api(username: str = Form(...), password: str = Form(...)):
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username or password is required")
    if Path(cache / f"admin/admin-create-{username}.json").exists():
        with open(cache / f"admin/admin-create-{username}.json", "r") as f:
            data = json.load(f)
    else:
        raise HTTPException(status_code=404, detail="No admin file found")
    if not data["can_create"]:
        raise HTTPException(status_code=401, detail="Check /register/admin/help")
    if bcrypt.checkpw(password.encode("utf-8"), data["password"].encode("utf-8")) and data["username"] == username:
        create_user_hashed_password(username, data["password"], "admin")
        (cache / f"admin/admin-create-{username}.json").unlink()
        return "User created successfully"
    else:
        raise HTTPException(status_code=400, detail="Incorrect username or password")


@app.delete("/user/{username}")
def delete_user_api(username: str, user=Depends(verify_admin_token)):
    if not(user["role"] == "admin" or user["sub"] == username):
        raise HTTPException(status_code=403, detail="No permission")
    delete_user(username)
    return {"message": "User successfully deleted"}


@app.get("/user/{username}")
def get_user_api(username: str, user=Depends(verify_admin_token)):
    usr = get_user_by_username(username)
    if not usr:
        raise HTTPException(status_code=404, detail="User not found")
    return usr


@app.get("/user")
def get_all_users_api(user=Depends(verify_admin_token)):
    return {"users": get_all_users()}


@app.get("/protected")
def protected_api(user=Depends(verify_token)):
    return {"message": user}

@app.get("/process")
def get_process_api(user=Depends(verify_token)):
    process_id = []
    for process in get_all_processes():
        process_id.append(process.id)
    return {"process": process_id}

@app.post("/process")
def create_process_api(user=Depends(verify_token), type: str=Form(...), playlist: str=Form(...), title: str=Form(...), process: str=Form(...), private: bool=Form(...)):
    created_process = create_process(user["sub"], process, private, title, type, playlist)
    return {"message": "Process created successfully", "process_id": created_process}

@app.get("/process/{process_id}")
def get_process_api(process_id: str, user=Depends(verify_token)):
    int_process_id = uuid.UUID(process_id)
    sel_process = get_process(int_process_id)
    if not sel_process:
        raise HTTPException(status_code=404, detail="Process not found")
    owned = sel_process.owner == user["sub"]
    if not owned and sel_process.private:
        data = {
            "videos": [],
            "id": sel_process.id,
            "title": "",
            "playlist": "",
            "private": True,
            "finished": sel_process.finished,
            "owner": sel_process.owner,
            "type": sel_process.type,
            "can_see": False
        }
        return data
    data = {
        "videos": sel_process.videos,
        "id": sel_process.id,
        "title": sel_process.title,
        "playlist": sel_process.playlist,
        "private": sel_process.private,
        "finished": sel_process.finished,
        "owner": sel_process.owner,
        "type": sel_process.type,
        "can_see": True
    }
    return data

#Video managing
@app.get("/{token}/videos/{video_id}/thumbnail")
def get_remote_image_api(video_id: str):
    #First check cache
    thumb_path = Path(cache / f"videos/{video_id}/thumbnail.jpg")
    if thumb_path.exists():
        return FileResponse(
            thumb_path,
            media_type="image/jpeg"
        )
    with YoutubeDL(opts) as ydl:
        url = f"https://www.youtube.com/watch?v={video_id}"
        print(url)
        info = ydl.extract_info(url, download=False)

    r = requests.get(info.get("thumbnail"), stream=True)
    r.raise_for_status()
    vid = Path(cache / f"videos/{video_id}/")
    if not vid.exists():
        vid.mkdir(exist_ok=True, parents=True)
    with open(vid / "thumbnail.jpg", "wb") as f:
        f.write(r.content)

    return StreamingResponse(
        io.BytesIO(r.content),
        media_type="image/jpeg"
    )

@app.get("/videos")
def get_videos_api(user=Depends(verify_token)):
    vids = get_all_videos()
    video_ids = []
    for vid in vids:
        video_ids.append(vid.id)
    return {"videos": video_ids}

@app.get("/videos/{video_id}/detail")
def get_video_detail_api(video_id: str, user=Depends(verify_token)):
    vid_detail = Path(cache / f"videos/{video_id}")
    vid_detail.mkdir(exist_ok=True, parents=True)
    if Path(vid_detail / "detail.json").exists():
        info = json.loads(Path(vid_detail / "detail.json").read_text())
    else:
        with YoutubeDL(opts) as ydl:
            url = f"https://www.youtube.com/watch?v={video_id}"
            print(url)
            info = ydl.extract_info(url, download=False)

            with open(Path(vid_detail / "detail.json"), "w") as f:
                f.write(json.dumps(info))
    data = {
        "id": info["id"],
        "title": info["title"],
        "thumbnail": info["thumbnail"],
        "channel": info["channel"],
    }
    return data

@app.get("/playlist/{playlist_id}/detail")
def get_playlist_detail_api(playlist_id: str, user=Depends(verify_token)):
    vid_detail = Path(cache / f"playlists/{playlist_id}")
    vid_detail.mkdir(parents=True, exist_ok=True)
    if Path(vid_detail / "detail.json").exists():
        info = json.loads(Path(vid_detail / "detail.json").read_text())
    else:
        with YoutubeDL(opts) as ydl:
            url = f"https://www.youtube.com/playlist?list={playlist_id}"
            print(url)
            info = ydl.extract_info(url, download=False)
            with open(Path(vid_detail / "detail.json"), "w") as f:
                f.write(json.dumps(info))
    vids = []
    for item in info["entries"]:
        vids.append(item["id"])
    return vids

@app.get("/{token}/videos/{video_id}")
def get_video_api(video_id: str, token: str):
    verify_token(token)
    vid = get_video(video_id)
    if not vid:
        raise HTTPException(status_code=404, detail="Video not found")
    vid_path = Path(vid.path)

    return FileResponse(
        path=str(vid_path),
        media_type="video/mp4",
        filename=f"{vid_path.name}"
    )

@app.websocket("/ws/progress")
async def progress_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "start":
                # Run send loop and message listener concurrently
                await asyncio.gather(
                    start_download_task(websocket),
                    listen_for_commands(websocket),
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def listen_for_commands(ws: WebSocket):
    while True:
        msg = await ws.receive_text()
        if msg == "stop":
            raise WebSocketDisconnect  # or use an asyncio.Event to signal stop

async def start_download_task(ws: WebSocket):
    while True:
        data = {
            "current_process": str(app.state["shared"]["current_process"]),
            "current_video_progress": app.state["shared"]["current_video_progress"],
            "current_process_progress": app.state["shared"]["current_process_progress"],
            "current_process_video_count": app.state["shared"]["current_process_video_count"],
            "process_eta": app.state["shared"]["process_eta"],
            "current_video_id": app.state["shared"]["current_video_id"],
        }
        await ws.send_json(data)
        await asyncio.sleep(0.25)

@app.get("/status")
def status_api(user=Depends(verify_token)):
    return {app.state["shared"]}