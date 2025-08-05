from typing import Annotated, Optional
from fastapi import APIRouter, Body, Depends, Query

from app.models.admin import AdminModel
from app.shared.constant import SUPER_ADMIN
from app.shared.decorator import response_decorator
from app.domain.subject.entity import (
    ListSubjectRegistrationInResponse,
    StudentInSubject,
    SubjectRegistrationInCreateByAdmin,
    SubjectRegistrationInResponse,
)
from app.use_cases.subject_registration.registration import (
    SubjectRegistrationStudentCase,
    SubjectRegistrationStudentRequestObject,
)
from app.use_cases.subject_registration.list import (
    ListSubjectRegistrationsRequestObject,
    ListSubjectRegistrationsUseCase,
)
from app.domain.shared.enum import AdminRole, Sort
from app.use_cases.subject_registration.list_by_subject_id import (
    ListSubjectRegistrationsBySubjectIdRequestObject,
    ListSubjectRegistrationsBySubjectIdUseCase,
)
from app.infra.security.security_service import authorization, get_current_admin

router = APIRouter()


@router.get(
    "",
    response_model=ListSubjectRegistrationInResponse,
)
@response_decorator()
def get_subject_registration(
    list_subject_registration_use_case: ListSubjectRegistrationsUseCase = Depends(
        ListSubjectRegistrationsUseCase
    ),
    current_admin: AdminModel = Depends(get_current_admin),
    page_index: int = 1,
    page_size: Annotated[int, Query(title="Page size", le=500)] = 300,
    search: str | None = None,
    group: int | None = None,
    sort: Sort = Sort.ASCE,
    sort_by: str = "numerical_order",
    season: int | None = None,
):
    if sort_by in ["numerical_order", "season", "group"]:
        sort_by = f"seasons_info.{sort_by}"
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListSubjectRegistrationsRequestObject.builder(
        page_index=page_index,
        page_size=page_size,
        sort=sort_query,
        search=search,
        group=group,
        season=season,
        current_admin=current_admin,
    )
    response = list_subject_registration_use_case.execute(request_object=req_object)

    return response


@router.get(
    "/subject/{subject_id}",
    response_model=list[StudentInSubject],
)
@response_decorator()
def get_subject_registration_by_subject_id(
    subject_id: str,
    current_admin: AdminModel = Depends(get_current_admin),
    search: Optional[str] = Query(None, title="Search"),
    list_subject_registration_use_case: ListSubjectRegistrationsBySubjectIdUseCase = Depends(
        ListSubjectRegistrationsBySubjectIdUseCase
    ),
):
    req_object = ListSubjectRegistrationsBySubjectIdRequestObject.builder(
        subject_id=subject_id, current_admin=current_admin, search=search
    )
    response = list_subject_registration_use_case.execute(request_object=req_object)

    return response


@router.post("", response_model=SubjectRegistrationInResponse)
@response_decorator()
def subject_registration(
    payload: SubjectRegistrationInCreateByAdmin = Body(
        ..., title="Subject registration In Create payload"
    ),
    subject_registration_use_case: SubjectRegistrationStudentCase = Depends(
        SubjectRegistrationStudentCase
    ),
    current_admin: AdminModel = Depends(get_current_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BKL, AdminRole.BHV])
    req_object = SubjectRegistrationStudentRequestObject.builder(
        payload.subjects, payload.student_id, current_admin
    )
    response = subject_registration_use_case.execute(request_object=req_object)
    return response
