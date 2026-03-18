from fastapi import FastAPI
from products import router as products_router
from auth import router as auth_router
from headers_demo import router as headers_router
from models import UserCreate

app = FastAPI(title="FastAPI KR2", description="Контрольная работа №2")

app.include_router(products_router)
app.include_router(auth_router)
app.include_router(headers_router)

@app.get("/")
async def root():
    return {
        "message": "FastAPI KR2",
        "endpoints": [
            "POST /create_user",
            "GET /product/{product_id}",
            "GET /products/search",
            "POST /login",
            "GET /user",
            "POST /login-signed",
            "GET /profile",
            "GET /headers",
            "GET /info"
        ]
    }

@app.post("/create_user")
async def create_user(user: UserCreate):
    """Задание 3.1: Создание пользователя"""
    return user