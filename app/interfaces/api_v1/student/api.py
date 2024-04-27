from fastapi import APIRouter

from app.interfaces.api_v1.student import (
    auth,
    subject,
    subject_registration,
    subject_evaluation_question,
    subject_evaluation,
    absent,
    student,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth Student"])
api_router.include_router(student.router, prefix="", tags=["Student me"])
api_router.include_router(subject_registration.router, prefix="/subjects/registration", tags=["Subject Student"])
api_router.include_router(subject_evaluation.router, prefix="/subjects/evaluation", tags=["Subject Student"])
api_router.include_router(
    subject_evaluation_question.router,
    prefix="/subjects/evaluation-questions",
    tags=["Subject Student"],
)
api_router.include_router(subject.router, prefix="/subjects", tags=["Subject Student"])
api_router.include_router(absent.router, prefix="/absent", tags=["Absent Student"])
