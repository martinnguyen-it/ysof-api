from fastapi import APIRouter, Body, Depends, File, Path, Query, UploadFile
from typing import Annotated, Optional
from app.domain.admin.entity import (
    Admin,
    AdminInCreate,
    AdminInDB,
    AdminInUpdate,
    AdminInUpdateMe,
    ManyAdminsInResponse,
)
from app.domain.shared.enum import Sort
from app.infra.security.security_service import (
    authorization,
    get_current_active_admin,
    get_current_admin,
)
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
from app.use_cases.admin.update_avatar import UpdateAvatarRequestObject, UpdateAvatarUseCase

router = APIRouter()


@router.get("/me", response_model=Admin)
def get_me(
    current_admin: AdminModel = Depends(get_current_admin),
):
    """
    get current admin data
    :param current_admin:
    :return:
    """
    return Admin(**AdminInDB.model_validate(current_admin).model_dump())


@router.get(
    "/{admin_id}",
    dependencies=[Depends(get_current_admin)],  # auth route
    response_model=Admin,
)
@response_decorator()
def get_admin_by_id(
    admin_id: str = Path(..., title="Admin id"),
    get_admin_use_case: GetAdminCase = Depends(GetAdminCase),
):
    get_admin_request_object = GetAdminRequestObject.builder(admin_id=admin_id)
    response = get_admin_use_case.execute(request_object=get_admin_request_object)
    return response


@router.post(
    "",
    response_model=Admin,
)
@response_decorator()
def create_admin(
    payload: AdminInCreate = Body(..., title="Admin In Create payload"),
    create_admin_use_case: CreateAdminUseCase = Depends(CreateAdminUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, SUPER_ADMIN)
    req_object = CreateAdminRequestObject.builder(payload=payload, current_admin=current_admin)
    response = create_admin_use_case.execute(request_object=req_object)
    return response


@router.get(
    "",
    response_model=ManyAdminsInResponse,
)
@response_decorator()
def get_list_admins(
    list_admins_use_case: ListAdminsUseCase = Depends(ListAdminsUseCase),
    page_index: Annotated[int, Query(title="Page Index")] = 1,
    page_size: Annotated[int, Query(title="Page size", le=300)] = 100,
    search: Optional[str] = Query(None, title="Search"),
    sort: Optional[Sort] = Sort.DESC,
    sort_by: Optional[str] = "id",
    season: Optional[int] = None,
    current_admin: AdminModel = Depends(get_current_admin),
):
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}
    req_object = ListAdminsRequestObject.builder(
        page_index=page_index,
        page_size=page_size,
        search=search,
        current_admin=current_admin,
        season=season,
        sort=sort_query,
    )
    response = list_admins_use_case.execute(request_object=req_object)
    return response


@router.put(
    "/me",
    response_model=Admin,
)
@response_decorator()
def update_me(
    payload: AdminInUpdateMe = Body(..., title="Admin update me payload"),
    update_admin_use_case: UpdateAdminUseCase = Depends(UpdateAdminUseCase),
    current_admin: AdminModel = Depends(get_current_admin),
):
    req_object = UpdateAdminRequestObject.builder(
        id=str(current_admin.id), payload=payload, current_admin=current_admin
    )
    response = update_admin_use_case.execute(request_object=req_object)
    return response


@router.put("/me/avatar")
@response_decorator()
def update_avatar(
    image: UploadFile = File(...),
    upload_avatar_use_case: UpdateAvatarUseCase = Depends(UpdateAvatarUseCase),
    current_admin: AdminModel = Depends(get_current_admin),
):
    req_object = UpdateAvatarRequestObject.builder(image=image, current_admin=current_admin)
    response = upload_avatar_use_case.execute(request_object=req_object)
    return response


@router.put(
    "/{id}",
    response_model=Admin,
)
@response_decorator()
def update_admin(
    id: str = Path(..., title="Admin Id"),
    payload: AdminInUpdate = Body(..., title="Admin updated payload"),
    update_admin_use_case: UpdateAdminUseCase = Depends(UpdateAdminUseCase),
    current_admin: AdminModel = Depends(get_current_admin),
):
    """_summary_

    Args:
        id (str, optional):
            Defaults to Path(..., title="Admin Id").
        payload (AdminInUpdate, optional):
            Defaults to Body(..., title="Admin updated payload").
        update_admin_use_case (UpdateAdminUseCase, optional):
            Defaults to Depends( UpdateAdminUseCase).
        current_admin (AdminModel, optional):
            Defaults to Depends(get_current_admin).

    Raises:
        forbidden_exception:
            - If not super admin and not update the owner account
            - If not super admin and update the owner account, but have roles or status in payload
            - If role BDH and not current season and (not update the
                owner account or update roles or update status)
    Returns:
        _type_: Admin
    """
    if not str(current_admin.id) == id or payload.roles is not None or payload.status is not None:
        authorization(current_admin, SUPER_ADMIN, True)

    req_object = UpdateAdminRequestObject.builder(
        id=id, payload=payload, current_admin=current_admin
    )
    response = update_admin_use_case.execute(request_object=req_object)
    return response
