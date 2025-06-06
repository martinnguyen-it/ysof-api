from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.domain.roll_call.entity import StudentRollCallResultInStudentResponse
from app.infra.security.security_service import get_current_student
from app.models.student import StudentModel
from app.shared.decorator import response_decorator
from app.use_cases.roll_call.get_student_results import (
    GetStudentRollCallResultsRequestObject,
    GetStudentRollCallResultsUseCase,
)

router = APIRouter()


@router.get("/me", response_model=StudentRollCallResultInStudentResponse)
@response_decorator()
def get_my_roll_call_results(
    get_student_roll_call_results_use_case: GetStudentRollCallResultsUseCase = Depends(
        GetStudentRollCallResultsUseCase
    ),
    current_student: StudentModel = Depends(get_current_student),
    season: Optional[int] = Query(None, title="Season"),
):
    req_object = GetStudentRollCallResultsRequestObject.builder(
        current_student=current_student,
        season=season,
    )
    response = get_student_roll_call_results_use_case.execute(request_object=req_object)
    return response
