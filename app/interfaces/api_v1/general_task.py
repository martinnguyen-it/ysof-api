from fastapi import APIRouter, Body, Depends, Path, Query, HTTPException
from typing import Annotated, Optional

from app.domain.admin.entity import AdminInDB
from app.domain.general_task.entity import (GeneralTask, GeneralTaskInCreate, ManyGeneralTasksInResponse,
                                            GeneralTaskInUpdate)
from app.domain.shared.enum import Sort
from app.infra.security.security_service import authorization, get_current_active_admin
from app.shared.decorator import response_decorator
from app.use_cases.general_task.list import ListGeneralTasksUseCase, ListGeneralTasksRequestObject
from app.use_cases.general_task.update import UpdateGeneralTaskUseCase, UpdateGeneralTaskRequestObject
from app.use_cases.general_task.get import (
    GetGeneralTaskRequestObject,
    GetGeneralTaskCase,
)
from app.use_cases.general_task.create import (
    CreateGeneralTaskRequestObject,
    CreateGeneralTaskUseCase,
)
from app.models.admin import AdminModel
from app.shared.constant import SUPER_ADMIN
from app.use_cases.general_task.delete import DeleteGeneralTaskRequestObject, DeleteGeneralTaskUseCase

router = APIRouter()


@router.get(
    "/{general_task_id}",
    dependencies=[Depends(get_current_active_admin)],
    response_model=GeneralTask,
)
@response_decorator()
def get_general_task_by_id(
        general_task_id: str = Path(..., title="GeneralTask id"),
        get_general_task_use_case: GetGeneralTaskCase = Depends(
            GetGeneralTaskCase),
):
    get_general_task_request_object = GetGeneralTaskRequestObject.builder(
        general_task_id=general_task_id)
    response = get_general_task_use_case.execute(
        request_object=get_general_task_request_object)
    return response


@router.post(
    "",
    response_model=GeneralTask,
)
@response_decorator()
def create_general_task(
        payload: GeneralTaskInCreate = Body(...,
                                            title="GeneralTask In Create payload"),
        create_general_task_use_case: CreateGeneralTaskUseCase = Depends(
            CreateGeneralTaskUseCase),
        current_admin: AdminInDB = Depends(get_current_active_admin),
):
    if payload.role not in current_admin.roles:
        authorization(current_admin, SUPER_ADMIN)
    req_object = CreateGeneralTaskRequestObject.builder(
        payload=payload, author=current_admin)
    response = create_general_task_use_case.execute(request_object=req_object)
    return response


@router.get(
    "",
    response_model=ManyGeneralTasksInResponse,
)
@response_decorator()
def get_list_general_tasks(
        list_general_tasks_use_case: ListGeneralTasksUseCase = Depends(
            ListGeneralTasksUseCase),
        page_index: Annotated[int, Query(title="Page Index")] = 1,
        page_size: Annotated[int, Query(title="Page size")] = 100,
        search: Optional[str] = Query(None, title="Search"),
        label: Optional[list[str]] = Query(None, title="Labels"),
        roles: Optional[list[str]] = Query(None, title="Roles"),
        sort: Optional[Sort] = Sort.DESC,
        sort_by: Optional[str] = 'id',
        current_admin: AdminModel = Depends(get_current_active_admin)
):
    annotations = {}
    for base in reversed(GeneralTask.__mro__):
        annotations.update(getattr(base, '__annotations__', {}))
    if sort_by not in annotations:
        raise HTTPException(
            status_code=400, detail=f"Invalid sort_by: {sort_by}")
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListGeneralTasksRequestObject.builder(author=current_admin,
                                                       page_index=page_index,
                                                       page_size=page_size,
                                                       search=search,
                                                       label=label,
                                                       roles=roles,
                                                       sort=sort_query)
    response = list_general_tasks_use_case.execute(request_object=req_object)
    return response


@router.put(
    "/{id}",
    response_model=GeneralTask,
)
@response_decorator()
def update_general_task(
        id: str = Path(..., title="GeneralTask Id"),
        payload: GeneralTaskInUpdate = Body(...,
                                            title="GeneralTask updated payload"),
        update_general_task_use_case: UpdateGeneralTaskUseCase = Depends(
            UpdateGeneralTaskUseCase),
        current_admin: AdminModel = Depends(get_current_active_admin),
):
    if payload.role and payload.role not in current_admin.roles:
        authorization(current_admin, SUPER_ADMIN)

    req_object = UpdateGeneralTaskRequestObject.builder(
        id=id, payload=payload, admin_roles=current_admin.roles)
    response = update_general_task_use_case.execute(request_object=req_object)
    return response


@router.delete("/{id}")
@response_decorator()
def delete_general_task(
        id: str = Path(..., title="GeneralTask Id"),
        delete_general_task_use_case: DeleteGeneralTaskUseCase = Depends(
            DeleteGeneralTaskUseCase),
        current_admin: AdminModel = Depends(get_current_active_admin),
):
    req_object = DeleteGeneralTaskRequestObject.builder(
        id=id, admin_roles=current_admin.roles)
    response = delete_general_task_use_case.execute(request_object=req_object)
    return response
