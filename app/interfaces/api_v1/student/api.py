from fastapi import APIRouter

from app.interfaces.api_v1.student import auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth Student"])
