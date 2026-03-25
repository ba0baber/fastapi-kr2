from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone
from enum import Enum

app = FastAPI(title="7.1")
bearer_security = HTTPBearer()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

SECRET_KEY = "rbac-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

fake_users_db = {}

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.USER 

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    role: UserRole

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_security)):
    payload = decode_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = fake_users_db.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def require_role(required_roles: list[UserRole]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {required_roles}"
            )
        return current_user
    return role_checker

fake_users_db["admin"] = {
    "username": "admin",
    "hashed_password": get_password_hash("admin123"),
    "role": UserRole.ADMIN
}

fake_users_db["guest_user"] = {
    "username": "guest_user",
    "hashed_password": get_password_hash("guest123"),
    "role": UserRole.GUEST
}

@app.post("/register", status_code=201)
def register(user: UserCreate, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Только ADMIN может регистрировать новых пользователей"""
    if user.username in fake_users_db:
        raise HTTPException(status_code=409, detail="User already exists")
    
    fake_users_db[user.username] = {
        "username": user.username,
        "hashed_password": get_password_hash(user.password),
        "role": user.role
    }
    return {"message": f"User {user.username} created with role {user.role}"}

@app.post("/login", response_model=TokenResponse)
def login(user: UserCreate):
    """Логин - доступен всем"""
    db_user = fake_users_db.get(user.username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(data={"sub": user.username})
    return TokenResponse(access_token=token)

@app.get("/protected_resource")
def protected_resource(current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.USER]))):
    """Доступ только для ADMIN и USER"""
    return {
        "message": "Access granted to protected resource",
        "user": current_user["username"],
        "role": current_user["role"]
    }

@app.get("/admin_only")
def admin_only(current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Только для ADMIN"""
    return {
        "message": "Welcome to admin panel",
        "admin": current_user["username"]
    }

@app.get("/read_only")
def read_only(current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.USER, UserRole.GUEST]))):
    """Доступ для всех аутентифицированных пользователей"""
    return {
        "message": "Read-only resource",
        "user": current_user["username"],
        "role": current_user["role"]
    }

@app.get("/users")
def list_users(current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Только ADMIN может видеть список всех пользователей"""
    users_list = []
    for username, user_data in fake_users_db.items():
        users_list.append({
            "username": username,
            "role": user_data["role"]
        })
    return {"users": users_list}
