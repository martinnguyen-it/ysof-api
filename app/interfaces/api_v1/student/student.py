from fastapi import APIRouter, Depends
from app.domain.student.entity import Student, StudentInDB
from app.models.student import StudentModel
from app.infra.security.security_service import get_current_student

router = APIRouter()


@router.get("/me", response_model=Student)
def get_me(
    current_student: StudentModel = Depends(get_current_student),
):
    return Student(**StudentInDB.model_validate(current_student).model_dump())
