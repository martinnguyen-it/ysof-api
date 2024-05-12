from fastapi import APIRouter, Depends

from app.shared.decorator import response_decorator
from app.domain.subject.entity import ListSubjectRegistrationInResponse, StudentInSubject
from app.use_cases.subject_registration.list import (
    ListSubjectRegistrationsRequestObject,
    ListSubjectRegistrationsUseCase,
)
from app.domain.shared.enum import Sort
from app.use_cases.subject_registration.list_by_subject_id import (
    ListSubjectRegistrationsBySubjectIdRequestObject,
    ListSubjectRegistrationsBySubjectIdUseCase,
)
from app.infra.security.security_service import get_current_active_admin

router = APIRouter()


@router.get("", response_model=ListSubjectRegistrationInResponse, dependencies=[Depends(get_current_active_admin)])
@response_decorator()
def get_subject_registration(
    list_subject_registration_use_case: ListSubjectRegistrationsUseCase = Depends(ListSubjectRegistrationsUseCase),
    page_index: int = 1,
    page_size: int = 300,
    search: str | None = None,
    group: int | None = None,
    sort: Sort = Sort.ASCE,
    sort_by: str = "numerical_order",
):
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}
    req_object = ListSubjectRegistrationsRequestObject.builder(
        page_index=page_index, page_size=page_size, sort=sort_query, search=search, group=group
    )
    response = list_subject_registration_use_case.execute(request_object=req_object)

    return response


@router.get(
    "/subject/{subject_id}",
    response_model=list[StudentInSubject],
    dependencies=[Depends(get_current_active_admin)],
)
@response_decorator()
def get_subject_registration_by_subject_id(
    subject_id: str,
    list_subject_registration_use_case: ListSubjectRegistrationsBySubjectIdUseCase = Depends(
        ListSubjectRegistrationsBySubjectIdUseCase
    ),
):
    req_object = ListSubjectRegistrationsBySubjectIdRequestObject.builder(subject_id=subject_id)
    response = list_subject_registration_use_case.execute(request_object=req_object)

    return response
