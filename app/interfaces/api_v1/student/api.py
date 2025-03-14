from fastapi import APIRouter

from app.interfaces.api_v1.student import (
    auth,
    daily_bible,
    subject,
    subject_registration,
    subject_evaluation_question,
    subject_evaluation,
    absent,
    student,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["API Student - Auth"])
api_router.include_router(student.router, prefix="/students", tags=["API Student - Student by me"])
api_router.include_router(
    subject_registration.router, prefix="/subjects/registration", tags=["API Student - Subject"]
)
api_router.include_router(
    subject_evaluation.router, prefix="/subjects/evaluations", tags=["API Student - Subject"]
)
api_router.include_router(
    subject_evaluation_question.router,
    prefix="/subjects/evaluation-questions",
    tags=["API Student - Subject"],
)
api_router.include_router(subject.router, prefix="/subjects", tags=["API Student - Subject"])
api_router.include_router(absent.router, prefix="/absent", tags=["API Student - Absent"])
api_router.include_router(
    daily_bible.router, prefix="/daily-bible", tags=["API Student - Daily Bible"]
)
