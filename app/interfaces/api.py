from fastapi import APIRouter, Depends

from app.infra.security.security_service import get_current_active_admin
from app.interfaces.api_v1.admin import (
    admin,
    auth as auth_admin,
    student,
    upload,
    document,
    general_task,
    lecturer,
    subject,
    season,
)
from app.interfaces.api_v1.student import auth as auth_student

api_router = APIRouter()
api_router.include_router(auth_admin.router, prefix="/admin/auth", tags=["Auth Admin"])
api_router.include_router(season.router, prefix="/seasons", tags=["Seasons"])
api_router.include_router(admin.router, prefix="/admins", tags=["Admins"])
api_router.include_router(document.router, prefix="/documents", tags=["Documents"])
api_router.include_router(general_task.router, prefix="/general-tasks", tags=["General Tasks"])
api_router.include_router(lecturer.router, prefix="/lecturers", tags=["Lecturers"])
api_router.include_router(subject.router, prefix="/subjects", tags=["Subjects"])
api_router.include_router(student.router, prefix="/admin/students", tags=["Students by admin"])
api_router.include_router(
    upload.router, prefix="/upload", tags=["Upload"], dependencies=[Depends(get_current_active_admin)]
)
# api_router.include_router(user.router, prefix="/users", tags=["Users"])

api_router.include_router(auth_student.router, prefix="/student/auth", tags=["Auth Student"])
