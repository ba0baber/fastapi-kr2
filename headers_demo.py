from fastapi import APIRouter, Header, HTTPException, Response
from datetime import datetime

router = APIRouter()

@router.get("/headers")
async def get_headers(
    user_agent: str = Header(..., alias="User-Agent"),
    accept_language: str = Header(..., alias="Accept-Language")
):
    """Возвращает заголовки User-Agent и Accept-Language"""
    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }

@router.get("/info")
async def get_info(
    response: Response,
    user_agent: str = Header(..., alias="User-Agent"),
    accept_language: str = Header(..., alias="Accept-Language")
):
    """Возвращает информацию о заголовках с дополнительным полем"""
    response.headers["X-Server-Time"] = datetime.now().isoformat()

    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": {
            "User-Agent": user_agent,
            "Accept-Language": accept_language
        }
    }