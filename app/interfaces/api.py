from fastapi import APIRouter, Depends

from app.infra.security.security_service import get_current_active_admin
from app.interfaces.api_v1.admin import (
    admin,
    auth,
    student,
    upload,
    document,
    general_task,
    lecturer,
    subject,
    season,
    audit_log,
)
from app.interfaces.api_v1.student import api as api_student

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/admin/auth", tags=["Auth Admin"])
api_router.include_router(season.router, prefix="/seasons", tags=["Seasons"])
api_router.include_router(admin.router, prefix="/admins", tags=["Admins"])
api_router.include_router(document.router, prefix="/documents", tags=["Documents"])
api_router.include_router(general_task.router, prefix="/general-tasks", tags=["General Tasks"])
api_router.include_router(lecturer.router, prefix="/lecturers", tags=["Lecturers"])
api_router.include_router(subject.router, prefix="/subjects", tags=["Subjects"])
api_router.include_router(student.router, prefix="/students", tags=["Students by admin"])
api_router.include_router(
    upload.router, prefix="/upload", tags=["Upload"], dependencies=[Depends(get_current_active_admin)]
)
api_router.include_router(audit_log.router, prefix="/audit-logs", tags=["Audit logs"])


api_router.include_router(api_student.api_router, prefix="/student")
