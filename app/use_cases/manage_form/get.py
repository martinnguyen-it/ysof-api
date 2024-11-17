from fastapi import Depends, BackgroundTasks
from app.shared import request_object, use_case
from app.domain.manage_form.entity import CommonResponse
from app.infra.manage_form.manage_form_repository import ManageFormRepository
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.models.manage_form import ManageFormModel
from app.domain.manage_form.enum import FormStatus, FormType


class GetManageFormCommonRequestObject(request_object.ValidRequestObject):
    def __init__(self, type: FormType):
        self.type = type

    @classmethod
    def builder(cls, type: FormType) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not isinstance(type, str):
            invalid_req.add_error("type", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return GetManageFormCommonRequestObject(type=type)


class GetManageFormCommonUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        manage_form_repository: ManageFormRepository = Depends(ManageFormRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.manage_form_repository = manage_form_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: GetManageFormCommonRequestObject):
        doc: ManageFormModel | None = self.manage_form_repository.find_one(
            {"type": req_object.type}
        )

        if doc:
            return CommonResponse.model_validate(doc)
        else:
            return CommonResponse(status=FormStatus.INACTIVE)
