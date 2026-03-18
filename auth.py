from fastapi import APIRouter, Request, Response, HTTPException
from pydantic import BaseModel
import uuid
import time
from itsdangerous import URLSafeTimedSerializer
import os

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "baobape")
serializer = URLSafeTimedSerializer(SECRET_KEY)

users_db = {
    "user123": "password123"
}

class LoginData(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(response: Response, login_data: LoginData):
    if login_data.username in users_db and users_db[login_data.username] == login_data.password:
        session_token = str(uuid.uuid4())
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=3600,
            secure=False,
            samesite="lax"
        )
        return {"message": "Login successful", "username": login_data.username}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/user")
async def get_user(request: Request):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {
        "username": "user123",
        "email": "user@example.com",
        "profile": "User profile information"
    }

@router.post("/login-signed")
async def login_signed(response: Response, login_data: LoginData):
    if login_data.username in users_db and users_db[login_data.username] == login_data.password:
        user_id = str(uuid.uuid4())
        session_token = serializer.dumps({"user_id": user_id})
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=300,
            secure=False,
            samesite="lax"
        )
        return {"message": "Login successful", "user_id": user_id}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/profile")
async def get_profile(request: Request):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        data = serializer.loads(session_token, max_age=300)
        return {
            "user_id": data.get("user_id"),
            "username": "user123",
            "email": "user@example.com",
            "message": "Profile accessed successfully"
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired session")


def create_session_token(user_id: str, timestamp: int = None) -> str:
    """Создаёт подписанный токен с user_id и timestamp"""
    if timestamp is None:
        timestamp = int(time.time())
    data = f"{user_id}.{timestamp}"
    signature = serializer.dumps(data)
    return signature

def verify_session_token(token: str) -> tuple[str, int] | None:
    """Проверяет токен и возвращает (user_id, timestamp) или None"""
    try:
        data = serializer.loads(token, max_age=300)  
        parts = data.split('.')
        if len(parts) != 2:
            return None
        user_id, timestamp_str = parts
        timestamp = int(timestamp_str)
        return user_id, timestamp
    except Exception:
        return None

@router.post("/login-dynamic")
async def login_dynamic(response: Response, login_data: LoginData):
    """Вход с динамической сессией"""
    if login_data.username in users_db and users_db[login_data.username] == login_data.password:
        user_id = str(uuid.uuid4())
        current_time = int(time.time())
        
        session_token = create_session_token(user_id, current_time)
        
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=300,  
            secure=False,
            samesite="lax"
        )
        
        return {
            "message": "Login successful",
            "user_id": user_id,
            "expires_in": "5 minutes"
        }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/profile-dynamic")
async def get_profile_dynamic(request: Request, response: Response):
    """Защищённый маршрут с динамическим продлением сессии"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="No session token")
    
    result = verify_session_token(session_token)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_id, last_activity = result
    current_time = int(time.time())
    time_diff = current_time - last_activity
    
    
    if time_diff > 300:  
        raise HTTPException(status_code=401, detail="Session expired")
    

    should_extend = False
    status_message = ""
    
    if 180 <= time_diff < 300:  
        should_extend = True
        status_message = f"Session extended (+5 min). Last activity was {time_diff} seconds ago"
    elif time_diff < 180:  
        status_message = f"Session active. Last activity was {time_diff} seconds ago (no extension needed)"
    
    if should_extend:
        new_token = create_session_token(user_id, current_time)
        response.set_cookie(
            key="session_token",
            value=new_token,
            httponly=True,
            max_age=300,
            secure=False,
            samesite="lax"
        )
    
    return {
        "user_id": user_id,
        "username": "user123",
        "last_activity": last_activity,
        "current_time": current_time,
        "seconds_since_activity": time_diff,
        "session_status": status_message or "Session active",
        "session_extended": should_extend,
        "message": "Profile accessed successfully"
    }

@router.get("/session-info")
async def get_session_info(request: Request):
    """Вспомогательный маршрут для отладки - показывает информацию о текущей сессии"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        return {"message": "No active session"}
    
    result = verify_session_token(session_token)
    if not result:
        return {"message": "Invalid session"}
    
    user_id, last_activity = result
    current_time = int(time.time())
    time_diff = current_time - last_activity
    
    return {
        "user_id": user_id,
        "last_activity": last_activity,
        "current_time": current_time,
        "seconds_since_activity": time_diff,
        "minutes_since_activity": round(time_diff / 60, 1),
        "session_valid": time_diff <= 300,
        "time_remaining_seconds": max(0, 300 - time_diff),
        "should_extend": 180 <= time_diff < 300
    }