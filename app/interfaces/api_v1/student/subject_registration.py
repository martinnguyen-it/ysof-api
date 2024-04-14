from fastapi import APIRouter, Depends, Body

from app.infra.security.security_service import get_current_student
from app.shared.decorator import response_decorator
from app.models.student import StudentModel
from app.domain.subject.entity import SubjectRegistrationInCreate, SubjectRegistrationInResponse
from app.use_cases.student_endpoint.subject.subject_registration import (
    SubjectRegistrationStudentCase,
    SubjectRegistrationStudentRequestObject,
)
from app.use_cases.student_endpoint.subject.get_subject_registration import (
    GetSubjectRegistrationStudentCase,
    GetSubjectRegistrationStudentRequestObject,
)

router = APIRouter()


@router.post("", response_model=SubjectRegistrationInResponse)
@response_decorator()
def subject_registration(
    payload: SubjectRegistrationInCreate = Body(..., title="Subject registration In Create payload"),
    subject_registration_use_case: SubjectRegistrationStudentCase = Depends(SubjectRegistrationStudentCase),
    current_student: StudentModel = Depends(get_current_student),
):
    req_object = SubjectRegistrationStudentRequestObject.builder(
        subjects=payload.subjects, current_student=current_student
    )
    response = subject_registration_use_case.execute(request_object=req_object)
    return response


@router.get("")
@response_decorator()
def get_subject_registration(
    get_subject_registration_use_case: GetSubjectRegistrationStudentCase = Depends(GetSubjectRegistrationStudentCase),
    current_student: StudentModel = Depends(get_current_student),
):
    req_object = GetSubjectRegistrationStudentRequestObject.builder(student_id=current_student.id)
    response = get_subject_registration_use_case.execute(request_object=req_object)

    return response
