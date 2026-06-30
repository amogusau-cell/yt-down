import jose
from fastapi import HTTPException, Header
from jose import jwt
from datetime import datetime, timedelta, timezone
from db_helper import check_user_password, get_user_by_username

SECRET = "veryverysecret"


def verify_token(token: str = Header(...)):
    if not token:
        raise HTTPException(status_code=401, detail="No token")
    token = token.replace("Bearer ", "")

    try:
        data = jwt.decode(token, SECRET, algorithms=["HS256"])
        if not get_user_by_username(data["sub"]):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        return data
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_admin_token(token: str = Header(...)):
    if not token:
        raise HTTPException(status_code=401, detail="No token")
    token = token.replace("Bearer ", "")

    try:
        data = jwt.decode(token, SECRET, algorithms=["HS256"])
        if not get_user_by_username(data["sub"]):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        if not data["role"] == "admin":
            raise HTTPException(status_code=403, detail="No permission")
        return data
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

def create_user_token (username: str, password: str, role: str):
    if not check_user_password(username, password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    usr = get_user_by_username(username)
    payload = {
        "sub": username,
        "role": role,
        "iat": datetime.now(timezone.utc),
        "token_ver": usr.password_id
    }
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    return token