from fastapi import APIRouter, Body, Depends, Path, Query, HTTPException
from typing import Annotated, Optional
from app.domain.admin.entity import Admin, AdminInCreate, AdminInDB, ManyAdminsInResponse, AdminInUpdate
from app.domain.shared.enum import Sort
from app.infra.security.security_service import get_current_active_admin, authorization
from app.shared.decorator import response_decorator
from app.use_cases.admin.list import ListAdminsUseCase, ListAdminsRequestObject
from app.use_cases.admin.update import UpdateAdminUseCase, UpdateAdminRequestObject
from app.use_cases.admin.get import (
    GetAdminRequestObject,
    GetAdminCase,
)
from app.use_cases.admin.create import (
    CreateAdminRequestObject,
    CreateAdminUseCase,
)
from app.shared.constant import SUPER_ADMIN
from app.models.admin import AdminModel

router = APIRouter()


@router.get("/me", response_model=Admin)
async def get_me(
        current_admin: AdminModel = Depends(get_current_active_admin),
):
    """
    get current admin data
    :param current_admin:
    :return:
    """
    return Admin(**AdminInDB.model_validate(current_admin).model_dump())


@router.get(
    "/{admin_id}",
    dependencies=[Depends(get_current_active_admin)],  # auth route
    response_model=Admin,
)
@response_decorator()
def get_admin_by_id(
        admin_id: str = Path(..., title="Admin id"),
        get_admin_use_case: GetAdminCase = Depends(GetAdminCase),
):
    get_admin_request_object = GetAdminRequestObject.builder(admin_id=admin_id)
    response = get_admin_use_case.execute(
        request_object=get_admin_request_object)
    return response


@router.post(
    "",
    response_model=Admin,
)
@response_decorator()
def create_admin(
        payload: AdminInCreate = Body(..., title="Admin In Create payload"),
        create_admin_use_case: CreateAdminUseCase = Depends(
            CreateAdminUseCase),
        current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, SUPER_ADMIN)
    req_object = CreateAdminRequestObject.builder(payload=payload)
    response = create_admin_use_case.execute(request_object=req_object)
    return response


@router.get(
    "",
    response_model=ManyAdminsInResponse,
    dependencies=[Depends(get_current_active_admin)],
)
@response_decorator()
def get_list_admins(
        list_admins_use_case: ListAdminsUseCase = Depends(ListAdminsUseCase),
        page_index: Annotated[int, Query(title="Page Index")] = 1,
        page_size: Annotated[int, Query(title="Page size")] = 100,
        search: Optional[str] = Query(None, title="Search"),
        sort: Optional[Sort] = Sort.DESC,
        sort_by: Optional[str] = 'id'
):
    annotations = {}
    for base in reversed(Admin.__mro__):
        annotations.update(getattr(base, '__annotations__', {}))
    if sort_by not in annotations:
        raise HTTPException(
            status_code=400, detail=f"Invalid sort_by: {sort_by}")
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListAdminsRequestObject.builder(page_index=page_index, page_size=page_size, search=search,
                                                 sort=sort_query)
    response = list_admins_use_case.execute(request_object=req_object)
    return response


@router.put(
    "/{id}",
    response_model=Admin,
)
@response_decorator()
def update_admin(
        id: str = Path(..., title="Admin Id"),
        payload: AdminInUpdate = Body(..., title="Admin updated payload"),
        update_admin_use_case: UpdateAdminUseCase = Depends(
            UpdateAdminUseCase),
        current_admin: AdminModel = Depends(get_current_active_admin),
):
    if not str(current_admin.id) == id:
        authorization(current_admin, SUPER_ADMIN)

    req_object = UpdateAdminRequestObject.builder(id=id, payload=payload)
    response = update_admin_use_case.execute(request_object=req_object)
    return response
