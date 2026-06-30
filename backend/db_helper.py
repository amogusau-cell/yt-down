import json
import sqlite3
from pathlib import Path

import bcrypt
import sqlalchemy
from fastapi import HTTPException
from sqlalchemy import create_engine, String, Integer, ARRAY, JSON, UUID, Boolean, event
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker
from paths import config, db_path, config_json
import uuid

engine = create_engine(
    db_path,
    connect_args={
        "check_same_thread": False,
        "timeout": 10  # wait up to 10s instead of immediately failing
    }
)


@event.listens_for(engine, "connect")
def set_wal_mode(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA journal_mode=WAL")


#with open(config_json, "r") as f:
#    config_data = json.load(f)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, primary_key=True)
    password_hash: Mapped[str] = mapped_column(String)
    password_id: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String)


class Process(Base):
    __tablename__ = "processes"

    id: Mapped[str] = mapped_column(UUID, primary_key=True)
    owner: Mapped[str] = mapped_column(String)
    private: Mapped[bool] = mapped_column(Boolean)
    videos: Mapped[list[str]] = mapped_column(JSON)
    finished: Mapped[bool] = mapped_column(Boolean)

    title: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    playlist: Mapped[str] = mapped_column(String)


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    path: Mapped[str] = mapped_column(String)


Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)

def get_all_users():
    with SessionLocal() as session:
        return session.query(User).all()


def create_user_private(username, password_hash, role):
    with SessionLocal() as session:
        user = User(username=username, password_hash=password_hash, password_id=0, role=role)
        session.add(user)
        session.commit()


def delete_user(username):
    with SessionLocal() as session:
        user = session.query(User).filter(User.username == username).first()
        session.delete(user)
        session.commit()


def get_user_by_username(username):
    with SessionLocal() as session:
        user = session.query(User).filter(User.username == username).first()
        return user


def commit():
    with SessionLocal() as session:
        session.commit()


def create_user(username, password, role):
    with SessionLocal() as session:
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt)
        try:
            create_user_private(username, password_hash, role)
        except sqlalchemy.exc.IntegrityError:
            raise HTTPException(status_code=409, detail="User with this username already exists")


def create_user_hashed_password(username, password_hash, role):
    with SessionLocal() as session:
        try:
            create_user_private(username, password_hash, role)
        except sqlalchemy.exc.IntegrityError:
            raise HTTPException(status_code=409, detail="User with this username already exists")


def check_user_password(username, password) -> bool:
    with SessionLocal() as session:
        user = get_user_by_username(username)
        try:
            if bcrypt.checkpw(password.encode("utf-8"), user.password_hash):
                return True
            else:
                return False
        except TypeError:
            if bcrypt.checkpw(password.encode("utf-8"), str(user.password_hash).encode("utf-8")):
                return True
            else:
                return False


def get_all_processes():
    with SessionLocal() as session:
        return session.query(Process).all()


def create_process(owner, videos, private, title, type, playlist):
    with SessionLocal() as session:
        process = Process(id=uuid.uuid4(), owner=owner, videos=videos, private=private, finished=False, title=title,
                          type=type, playlist=playlist)
        session.add(process)
        session.commit()
        return process.id


def delete_process(process_id):
    with SessionLocal() as session:
        process = session.query(Process).filter(Process.id == process_id).first()
        session.delete(process)
        session.commit()


def get_process(process_id):
    with SessionLocal() as session:
        process = session.query(Process).filter(Process.id == process_id).first()
        return process


def set_process_finished(process_id):
    with SessionLocal() as session:
        process = session.query(Process).filter(Process.id == process_id).first()
        process.finished = True
        session.commit()


def create_video(vid_id: str, path: str):
    with SessionLocal() as session:
        video = Video(id=vid_id, path=path)
        session.add(video)
        session.commit()


def get_video(vid_id):
    with SessionLocal() as session:
        video = session.query(Video).filter(Video.id == vid_id).first()
        return video


def get_all_videos():
    with SessionLocal() as session:
        return session.query(Video).all()


def delete_video(vid_id):
    with SessionLocal() as session:
        video = session.query(Video).filter(Video.id == vid_id).first()
        session.delete(video)
        session.commit()
