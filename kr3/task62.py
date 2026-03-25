from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
import secrets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="6.2")
security = HTTPBasic()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

fake_users_db = {}

class UserBase(BaseModel):
    username: str

class User(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

def auth_user(credentials: HTTPBasicCredentials = Depends(security)):
    logger.info(f"Attempting to authenticate user: {credentials.username}")
    user = fake_users_db.get(credentials.username)
    
    if not user:
        logger.warning(f"User not found: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    if not secrets.compare_digest(credentials.username, user["username"]):
        logger.warning(f"Username mismatch for: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    try:
        is_valid = pwd_context.verify(credentials.password, user["hashed_password"])
        if not is_valid:
            logger.warning(f"Invalid password for: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    logger.info(f"User authenticated: {credentials.username}")
    return user

@app.post("/register")
def register(user: User):
    logger.info(f"Registering user: {user.username}")
    
    if user.username in fake_users_db:
        logger.warning(f"User already exists: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    try:
        hashed = pwd_context.hash(user.password)
        logger.info(f"Password hashed successfully for: {user.username}")
        
        fake_users_db[user.username] = {
            "username": user.username,
            "hashed_password": hashed
        }
        
        logger.info(f"User registered successfully: {user.username}")
        return {"message": "User registered successfully"}
        
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.get("/login")
def login(current_user: dict = Depends(auth_user)):
    return {"message": f"Welcome, {current_user['username']}!"}

@app.get("/users")
def list_users():
    """Debug endpoint to see registered users"""
    return {"users": list(fake_users_db.keys())}
