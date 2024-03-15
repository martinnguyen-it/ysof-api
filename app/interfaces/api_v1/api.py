from fastapi import APIRouter

from app.interfaces.api_v1 import admin, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/admin/auth", tags=["Auth Admin"])
api_router.include_router(admin.router, prefix="/admins", tags=["Admins"])
# api_router.include_router(user.router, prefix="/users", tags=["Users"])

