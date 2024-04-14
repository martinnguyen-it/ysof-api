from fastapi import Depends, BackgroundTasks
from app.shared import request_object, use_case
from app.domain.manage_form.entity import CommonUpdate, FormUpdateWithTime, ManageFormInDB
from app.models.admin import AdminModel
from app.infra.manage_form.manage_form_repository import ManageFormRepository
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.models.manage_form import ManageFormModel
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.shared.utils.general import get_current_season_value
import json


class UpdateManageFormCommonRequestObject(request_object.ValidRequestObject):
    def __init__(self, payload: CommonUpdate, current_admin: AdminModel):
        self.payload = payload
        self.current_admin = current_admin

    @classmethod
    def builder(cls, payload: CommonUpdate, current_admin: AdminModel) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not isinstance(payload.status, str):
            invalid_req.add_error("status", "Invalid")
        if not isinstance(payload.type, str):
            invalid_req.add_error("type", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateManageFormCommonRequestObject(payload=payload, current_admin=current_admin)


class UpdateManageFormCommonUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        manage_form_repository: ManageFormRepository = Depends(ManageFormRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.manage_form_repository = manage_form_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: UpdateManageFormCommonRequestObject):
        doc: ManageFormModel | None = self.manage_form_repository.find_one({"type": req_object.payload.type})

        if doc:
            if doc.status == req_object.payload.status:
                return ManageFormInDB.model_validate(doc)

            res = self.manage_form_repository.update(
                id=doc.id, data=FormUpdateWithTime(**req_object.payload.model_dump())
            )
            if res:
                doc.reload()
                self.background_tasks.add_task(
                    self.audit_log_repository.create,
                    AuditLogInDB(
                        type=AuditLogType.UPDATE,
                        endpoint=Endpoint.MANAGE_FORM,
                        season=get_current_season_value(),
                        author=req_object.current_admin,
                        author_email=req_object.current_admin.email,
                        author_name=req_object.current_admin.full_name,
                        author_roles=req_object.current_admin.roles,
                        description=json.dumps(req_object.payload.model_dump(exclude_none=True), default=str),
                    ),
                )
                return ManageFormInDB.model_validate(doc)
            else:
                return ManageFormInDB.model_validate(doc)
        else:
            doc = self.manage_form_repository.create(ManageFormInDB(**req_object.payload.model_dump()))
            self.background_tasks.add_task(
                self.audit_log_repository.create,
                AuditLogInDB(
                    type=AuditLogType.CREATE,
                    endpoint=Endpoint.MANAGE_FORM,
                    season=get_current_season_value(),
                    author=req_object.current_admin,
                    author_email=req_object.current_admin.email,
                    author_name=req_object.current_admin.full_name,
                    author_roles=req_object.current_admin.roles,
                    description=json.dumps(req_object.payload.model_dump(exclude_none=True), default=str),
                ),
            )
            return ManageFormInDB.model_validate(doc)
