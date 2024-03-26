from fastapi import APIRouter, Body, Depends, Path, Query, HTTPException, UploadFile, File
from typing import Annotated, Optional

from app.domain.subject.entity import Subject, SubjectInCreate, ManySubjectsInResponse, \
    SubjectInUpdate
from app.domain.shared.enum import AdminRole, Sort
from app.infra.security.security_service import authorization, get_current_active_admin
from app.shared.decorator import response_decorator
# from app.use_cases.subject.list import ListSubjectsUseCase, ListSubjectsRequestObject
# from app.use_cases.subject.update import UpdateSubjectUseCase, UpdateSubjectRequestObject
# from app.use_cases.subject.get import (
#     GetSubjectRequestObject,
#     GetSubjectCase,
# )
from app.use_cases.subject.create import (
    CreateSubjectRequestObject,
    CreateSubjectUseCase,
)
from app.models.admin import AdminModel
from app.shared.constant import SUPER_ADMIN
# from app.use_cases.subject.delete import DeleteSubjectRequestObject, DeleteSubjectUseCase

router = APIRouter()


# @router.get(
#     "/{subject_id}",
#     dependencies=[Depends(get_current_active_admin)],
#     response_model=Subject,
# )
# @response_decorator()
# def get_subject_by_id(
#         subject_id: str = Path(..., title="Subject id"),
#         get_subject_use_case: GetSubjectCase = Depends(GetSubjectCase),
# ):
#     get_subject_request_object = GetSubjectRequestObject.builder(
#         subject_id=subject_id)
#     response = get_subject_use_case.execute(
#         request_object=get_subject_request_object)
#     return response


@router.post(
    "",
    response_model=Subject,
)
@response_decorator()
def create_subject(
        payload: SubjectInCreate = Body(...,
                                        title="Subject In Create payload"),
        create_subject_use_case: CreateSubjectUseCase = Depends(
            CreateSubjectUseCase),
        current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BHV])
    req_object = CreateSubjectRequestObject.builder(payload=payload)
    response = create_subject_use_case.execute(request_object=req_object)
    return response


# @router.get(
#     "",
#     response_model=ManySubjectsInResponse,
# )
# @response_decorator()
# def get_list_subjects(
#         list_subjects_use_case: ListSubjectsUseCase = Depends(
#             ListSubjectsUseCase),
#         page_index: Annotated[int, Query(title="Page Index")] = 1,
#         page_size: Annotated[int, Query(title="Page size")] = 100,
#         search: Optional[str] = Query(None, title="Search"),
#         label: Optional[list[str]] = Query(None, title="Labels"),
#         roles: Optional[list[str]] = Query(None, title="Roles"),
#         sort: Optional[Sort] = Sort.DESC,
#         sort_by: Optional[str] = 'id',
#         current_admin: AdminModel = Depends(get_current_active_admin)
# ):
#     annotations = {}
#     for base in reversed(Subject.__mro__):
#         annotations.update(getattr(base, '__annotations__', {}))
#     if sort_by not in annotations:
#         raise HTTPException(
#             status_code=400, detail=f"Invalid sort_by: {sort_by}")
#     sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

#     req_object = ListSubjectsRequestObject.builder(author=current_admin,
#                                                     page_index=page_index,
#                                                     page_size=page_size,
#                                                     search=search,
#                                                     label=label,
#                                                     roles=roles,
#                                                     sort=sort_query)
#     response = list_subjects_use_case.execute(request_object=req_object)
#     return response


# @router.put(
#     "/{id}",
#     response_model=Subject,
# )
# @response_decorator()
# def update_subject(
#         id: str = Path(..., title="Subject Id"),
#         payload: SubjectInUpdate = Body(...,
#                                          title="Subject updated payload"),
#         update_subject_use_case: UpdateSubjectUseCase = Depends(
#             UpdateSubjectUseCase),
#         current_admin: AdminModel = Depends(get_current_active_admin),
# ):
#     if payload.role and payload.role not in current_admin.roles:
#         authorization(current_admin, SUPER_ADMIN)

#     req_object = UpdateSubjectRequestObject.builder(
#         id=id, payload=payload, admin_roles=current_admin.roles)
#     response = update_subject_use_case.execute(request_object=req_object)
#     return response


# @router.delete("/{id}")
# @response_decorator()
# def delete_subject(
#         id: str = Path(..., title="Subject Id"),
#         delete_subject_use_case: DeleteSubjectUseCase = Depends(
#             DeleteSubjectUseCase),
#         current_admin: AdminModel = Depends(get_current_active_admin),
# ):
#     req_object = DeleteSubjectRequestObject.builder(
#         id=id, admin_roles=current_admin.roles)
#     response = delete_subject_use_case.execute(request_object=req_object)
#     return response
