from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from passlib.context import CryptContext
import secrets
import os
from dotenv import load_dotenv

load_dotenv()

MODE = os.getenv("MODE", "DEV")
DOCS_USER = os.getenv("DOCS_USER", "admin")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "docs123")

app = FastAPI(
    title="6.3",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

security = HTTPBasic()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

fake_users_db = {}

class User(BaseModel):
    username: str
    password: str

def verify_docs_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, DOCS_USER)
    correct_password = secrets.compare_digest(credentials.password, DOCS_PASSWORD)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials

def auth_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = fake_users_db.get(credentials.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    if not secrets.compare_digest(credentials.username, user["username"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    if not pwd_context.verify(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return user

@app.post("/register")
def register(user: User):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    fake_users_db[user.username] = {
        "username": user.username,
        "hashed_password": pwd_context.hash(user.password)
    }
    return {"message": "User registered successfully"}

@app.get("/login")
def login(current_user: dict = Depends(auth_user)):
    return {"message": f"Welcome, {current_user['username']}!"}

if MODE == "DEV":
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html(_=Depends(verify_docs_auth)):
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="API Documentation",
        )
    
    @app.get("/openapi.json", include_in_schema=False)
    async def custom_openapi_json(_=Depends(verify_docs_auth)):
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )
        return JSONResponse(openapi_schema)

elif MODE == "PROD":
    @app.get("/docs", include_in_schema=False)
    async def docs_not_found():
        raise HTTPException(status_code=404, detail="Not Found")
    
    @app.get("/openapi.json", include_in_schema=False)
    async def openapi_not_found():
        raise HTTPException(status_code=404, detail="Not Found")
    
    @app.get("/redoc", include_in_schema=False)
    async def redoc_not_found():
        raise HTTPException(status_code=404, detail="Not Found")
else:
    raise ValueError(f"Invalid MODE: {MODE}. Must be DEV or PROD")

@app.get("/")
def root():
    return {"status": "ok", "mode": MODE}
