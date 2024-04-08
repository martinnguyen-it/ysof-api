from fastapi import APIRouter, Body, Depends, Path, Query, HTTPException
from typing import Annotated, Optional

from app.domain.lecturer.entity import Lecturer, LecturerInCreate, LecturerInUpdate, ManyLecturersInResponse

from app.domain.shared.enum import AdminRole, Sort
from app.infra.security.security_service import authorization, get_current_active_admin, get_current_admin
from app.shared.decorator import response_decorator
from app.use_cases.lecturer.list import ListLecturersUseCase, ListLecturersRequestObject
from app.use_cases.lecturer.update import UpdateLecturerUseCase, UpdateLecturerRequestObject
from app.use_cases.lecturer.get import GetLecturerRequestObject, GetLecturerCase
from app.use_cases.lecturer.create import CreateLecturerRequestObject, CreateLecturerUseCase
from app.models.admin import AdminModel
from app.shared.constant import SUPER_ADMIN
from app.use_cases.lecturer.delete import DeleteLecturerRequestObject, DeleteLecturerUseCase

router = APIRouter()


@router.get(
    "/{lecturer_id}",
    dependencies=[Depends(get_current_admin)],
    response_model=Lecturer,
)
@response_decorator()
def get_lecturer_by_id(
    lecturer_id: str = Path(..., title="Lecturer id"),
    get_lecturer_use_case: GetLecturerCase = Depends(GetLecturerCase),
):
    get_lecturer_request_object = GetLecturerRequestObject.builder(lecturer_id=lecturer_id)
    response = get_lecturer_use_case.execute(request_object=get_lecturer_request_object)
    return response


@router.post("", response_model=Lecturer, name="Create lecturer - Role BHV")
@response_decorator()
def create_lecturer(
    payload: LecturerInCreate = Body(..., title="Lecturer In Create payload"),
    create_lecturer_use_case: CreateLecturerUseCase = Depends(CreateLecturerUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BHV])
    req_object = CreateLecturerRequestObject.builder(payload=payload, current_admin=current_admin)
    response = create_lecturer_use_case.execute(request_object=req_object)
    return response


@router.get(
    "",
    response_model=ManyLecturersInResponse,
    dependencies=[Depends(get_current_admin)],
)
@response_decorator()
def get_list_lecturers(
    list_lecturers_use_case: ListLecturersUseCase = Depends(ListLecturersUseCase),
    page_index: Annotated[int, Query(title="Page Index")] = 1,
    page_size: Annotated[int, Query(title="Page size")] = 100,
    search: Optional[str] = Query(None, title="Search"),
    sort: Optional[Sort] = Sort.DESC,
    sort_by: Optional[str] = "id",
):
    annotations = {}
    for base in reversed(Lecturer.__mro__):
        annotations.update(getattr(base, "__annotations__", {}))
    if sort_by not in annotations:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by: {sort_by}")
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListLecturersRequestObject.builder(
        page_index=page_index, page_size=page_size, search=search, sort=sort_query
    )
    response = list_lecturers_use_case.execute(request_object=req_object)
    return response


@router.put(
    "/{id}",
    response_model=Lecturer,
)
@response_decorator()
def update_lecturer(
    id: str = Path(..., title="Lecturer Id"),
    payload: LecturerInUpdate = Body(..., title="Lecturer updated payload"),
    update_lecturer_use_case: UpdateLecturerUseCase = Depends(UpdateLecturerUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BHV])
    req_object = UpdateLecturerRequestObject.builder(id=id, payload=payload, current_admin=current_admin)
    response = update_lecturer_use_case.execute(request_object=req_object)
    return response


@router.delete("/{id}")
@response_decorator()
def delete_lecturer(
    id: str = Path(..., title="Lecturer Id"),
    delete_lecturer_use_case: DeleteLecturerUseCase = Depends(DeleteLecturerUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, SUPER_ADMIN)
    req_object = DeleteLecturerRequestObject.builder(id=id, current_admin=current_admin)
    response = delete_lecturer_use_case.execute(request_object=req_object)
    return response
