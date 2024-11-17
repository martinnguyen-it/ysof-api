from fastapi import APIRouter, Depends, Body, Query
from app.infra.security.security_service import authorization, get_current_active_admin
from app.shared.decorator import response_decorator

from app.models.admin import AdminModel

from app.shared.constant import SUPER_ADMIN
from app.domain.shared.enum import AdminRole
from app.use_cases.manage_form.common_update import (
    UpdateManageFormCommonRequestObject,
    UpdateManageFormCommonUseCase,
)
from app.domain.manage_form.entity import CommonResponse, ManageFormBase
from app.use_cases.manage_form.get import (
    GetManageFormCommonRequestObject,
    GetManageFormCommonUseCase,
)
from app.domain.manage_form.enum import FormType

router = APIRouter()


@router.post("")
@response_decorator()
def manage_form(
    payload: ManageFormBase = Body(..., title="Manage form"),
    manage_form_common_use_case: UpdateManageFormCommonUseCase = Depends(
        UpdateManageFormCommonUseCase
    ),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    if payload.type == FormType.SUBJECT_ABSENT:
        authorization(current_admin, [*SUPER_ADMIN, AdminRole.BKL])
    elif payload.type == FormType.SUBJECT_EVALUATION:
        authorization(current_admin, [*SUPER_ADMIN, AdminRole.BHV])
    elif payload.type == FormType.SUBJECT_REGISTRATION:
        authorization(current_admin, [*SUPER_ADMIN, AdminRole.BHV, AdminRole.BKL])

    req_object = UpdateManageFormCommonRequestObject.builder(
        payload=payload, current_admin=current_admin
    )
    response = manage_form_common_use_case.execute(request_object=req_object)
    return response


@router.get("", response_model=CommonResponse)
@response_decorator()
def get_form(
    type: FormType = Query(..., title="Form type"),
    manage_form_common_use_case: GetManageFormCommonUseCase = Depends(GetManageFormCommonUseCase),
):
    req_object = GetManageFormCommonRequestObject.builder(type=type)
    response = manage_form_common_use_case.execute(request_object=req_object)
    return response
