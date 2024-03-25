from fastapi import APIRouter, Depends

from app.infra.security.security_service import get_current_active_admin
from app.interfaces.api_v1 import admin, auth, upload, document, general_task, lecturer

api_router = APIRouter()
api_router.include_router(
    auth.router, prefix="/admin/auth", tags=["Auth Admin"])
api_router.include_router(admin.router, prefix="/admins", tags=["Admins"])
api_router.include_router(
    document.router, prefix="/documents", tags=["Documents"])
api_router.include_router(
    general_task.router, prefix="/general-tasks", tags=["General Tasks"])
api_router.include_router(
    lecturer.router, prefix="/lecturers", tags=["Lecturers"])
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"],
                          dependencies=[Depends(get_current_active_admin)])
# api_router.include_router(user.router, prefix="/users", tags=["Users"])
