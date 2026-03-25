from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from database import init_db, create_user, get_user_by_username, get_all_users
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="8.1")

@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Database initialized")

class User(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: User):
    existing_user = get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    try:
        user_id = create_user(user.username, user.password)
        logger.info(f"User registered: {user.username} with id {user_id}")
        return {"message": "User registered successfully!"}
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@app.get("/users")
def list_users():
    users = get_all_users()
    return {"users": [dict(user) for user in users]}

@app.get("/users/{username}")
def get_user(username: str):
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return dict(user)

@app.get("/")
def root():
    return {"message": "Task 8.1 - SQLite Database API", "status": "running"}
