from fastapi import APIRouter, Depends, Body

from app.infra.security.security_service import authorization, get_current_active_admin
from app.shared.decorator import response_decorator

from app.models.admin import AdminModel

from app.shared.constant import SUPER_ADMIN
from app.domain.shared.enum import AdminRole
from app.use_cases.manage_form.common_update import UpdateManageFormCommonRequestObject, UpdateManageFormCommonUseCase
from app.domain.manage_form.entity import CommonUpdate, SubjectRegistrationUpdate
from app.domain.manage_form.enum import FormType
from app.use_cases.manage_form.get import GetManageFormCommonRequestObject, GetManageFormCommonUseCase

router = APIRouter()


@router.post("/subject-registration")
@response_decorator()
def manage_form_subject_registration(
    payload: SubjectRegistrationUpdate = Body(..., title="Manage form subject registration status"),
    manage_form_common_use_case: UpdateManageFormCommonUseCase = Depends(UpdateManageFormCommonUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BHV, AdminRole.BKT])
    req_object = UpdateManageFormCommonRequestObject.builder(
        payload=CommonUpdate(status=payload.status, type=FormType.SUBJECT_REGISTRATION), current_admin=current_admin
    )
    response = manage_form_common_use_case.execute(request_object=req_object)
    return response


@router.get("/subject-registration")
@response_decorator()
def get_form_subject_registration(
    manage_form_common_use_case: GetManageFormCommonUseCase = Depends(GetManageFormCommonUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BHV, AdminRole.BKT])
    req_object = GetManageFormCommonRequestObject.builder(type=FormType.SUBJECT_REGISTRATION)
    response = manage_form_common_use_case.execute(request_object=req_object)
    return response
