from fastapi import APIRouter, Body, Depends, File, Query, UploadFile
from app.domain.student.entity import (
    ManyStudentsInStudentRequestResponse,
    StudentGetMeResponse,
    StudentInDB,
    StudentUpdateMePayload,
)
from app.models.student import StudentModel
from app.infra.security.security_service import get_current_student
from app.shared.decorator import response_decorator
from typing import Annotated, Optional
from app.domain.shared.enum import Sort
from app.use_cases.student_endpoint.student.list import (
    ListStudentsInStudentRequestObject,
    ListStudentsInStudentRequestUseCase,
)
from app.use_cases.student_endpoint.student.update import (
    UpdateStudentMeRequestObject,
    UpdateStudentMeUseCase,
)
from app.use_cases.user.update_avatar import UpdateAvatarRequestObject, UpdateAvatarUseCase

router = APIRouter()


@router.get("/me", response_model=StudentGetMeResponse)
@response_decorator()
def get_me(
    current_student: StudentModel = Depends(get_current_student),
):
    return StudentGetMeResponse(**StudentInDB.model_validate(current_student).model_dump())


@router.put(
    "/me",
    response_model=StudentGetMeResponse,
)
@response_decorator()
def update_me(
    payload: StudentUpdateMePayload = Body(..., title="Student update me payload"),
    update_student_me_use_case: UpdateStudentMeUseCase = Depends(UpdateStudentMeUseCase),
    current_student: StudentModel = Depends(get_current_student),
):
    req_object = UpdateStudentMeRequestObject.builder(
        payload=payload, current_student=current_student
    )
    response = update_student_me_use_case.execute(request_object=req_object)
    return response


@router.put("/me/avatar", response_model=StudentGetMeResponse)
@response_decorator()
def update_avatar(
    image: UploadFile = File(...),
    upload_avatar_use_case: UpdateAvatarUseCase = Depends(UpdateAvatarUseCase),
    current_student: StudentModel = Depends(get_current_student),
):
    req_object = UpdateAvatarRequestObject.builder(image=image, user=current_student)
    response = upload_avatar_use_case.execute(request_object=req_object)
    return response


@router.get("", response_model=ManyStudentsInStudentRequestResponse)
@response_decorator()
def get_list_students(
    list_students_use_case: ListStudentsInStudentRequestUseCase = Depends(
        ListStudentsInStudentRequestUseCase
    ),
    page_index: Annotated[int, Query(title="Page Index")] = 1,
    page_size: Annotated[int, Query(title="Page size", le=500)] = 300,
    search: Optional[str] = Query(None, title="Search"),
    sort: Optional[Sort] = Sort.ASCE,
    sort_by: Optional[str] = "numerical_order",
    group: Optional[int] = None,
    current_student: StudentModel = Depends(get_current_student),
    season: int | None = None,
):
    if sort_by in ["numerical_order", "season", "group"]:
        sort_by = f"seasons_info.{sort_by}"
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListStudentsInStudentRequestObject.builder(
        page_index=page_index,
        page_size=page_size,
        search=search,
        sort=sort_query,
        group=group,
        current_student=current_student,
        season=season,
    )
    response = list_students_use_case.execute(request_object=req_object)
    return response
