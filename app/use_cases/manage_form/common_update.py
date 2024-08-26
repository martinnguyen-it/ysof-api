from datetime import timezone, datetime
from fastapi import Depends, BackgroundTasks, HTTPException
from pydantic import ValidationError
from app.shared import request_object, use_case, response_object
from app.domain.manage_form.entity import (
    ManageFormBase,
    ManageFormEvaluationOrAbsentInPayload,
    ManageFormInDB,
    ManageFormUpdateWithTime,
)
from app.models.admin import AdminModel
from app.infra.manage_form.manage_form_repository import ManageFormRepository
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.models.manage_form import ManageFormModel
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.shared.utils.general import get_current_season_value
import json
from app.domain.manage_form.enum import FormType
from app.infra.subject.subject_repository import SubjectRepository
from app.domain.subject.enum import StatusSubjectEnum


class UpdateManageFormCommonRequestObject(request_object.ValidRequestObject):
    def __init__(self, payload: ManageFormBase, current_admin: AdminModel):
        self.payload = payload
        self.current_admin = current_admin

    @classmethod
    def builder(cls, payload: ManageFormBase, current_admin: AdminModel) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not isinstance(payload.type, str):
            invalid_req.add_error("type", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateManageFormCommonRequestObject(payload=payload, current_admin=current_admin)


class UpdateManageFormCommonUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        manage_form_repository: ManageFormRepository = Depends(ManageFormRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.manage_form_repository = manage_form_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository
        self.subject_repository = subject_repository

    def process_request(self, req_object: UpdateManageFormCommonRequestObject):
        doc: ManageFormModel | None = self.manage_form_repository.find_one({"type": req_object.payload.type})

        if doc:
            if (
                req_object.payload.type in [FormType.SUBJECT_EVALUATION, FormType.SUBJECT_ABSENT]
                and req_object.payload.data
                and "subject_id" in req_object.payload.data
            ):
                subject = self.subject_repository.get_by_id(subject_id=req_object.payload.data["subject_id"])
                if not subject:
                    return response_object.ResponseFailure.build_not_found_error(message="Môn học không tồn tại")
                if req_object.payload.type == FormType.SUBJECT_ABSENT:
                    if subject.status == StatusSubjectEnum.INIT:
                        self.subject_repository.update(
                            id=subject.id,
                            data={
                                "status": StatusSubjectEnum.SENT_NOTIFICATION,
                                "updated_at": datetime.now(timezone.utc),
                            },
                        )
                else:
                    if subject.status != StatusSubjectEnum.SENT_EVALUATION:
                        self.subject_repository.update(
                            id=subject.id,
                            data={
                                "status": StatusSubjectEnum.SENT_EVALUATION,
                                "updated_at": datetime.now(timezone.utc),
                            },
                        )

            if doc.status == req_object.payload.status and doc.data == req_object.payload.data:
                return ManageFormInDB.model_validate(doc)

            res = self.manage_form_repository.update(
                id=doc.id, data=ManageFormUpdateWithTime(**req_object.payload.model_dump())
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
                        description=json.dumps(
                            req_object.payload.model_dump(exclude_none=True), default=str, ensure_ascii=False
                        ),
                    ),
                )
                return ManageFormInDB.model_validate(doc)
            else:
                return ManageFormInDB.model_validate(doc)
        else:
            if req_object.payload.type in [FormType.SUBJECT_EVALUATION, FormType.SUBJECT_ABSENT]:
                try:
                    _data = ManageFormEvaluationOrAbsentInPayload(
                        **req_object.payload.model_dump(exclude={"data"}),
                        data=req_object.payload.data if req_object.payload.data is not None else ({}),
                    )
                    subject = self.subject_repository.get_by_id(subject_id=_data.data.subject_id)
                    if not subject:
                        return response_object.ResponseFailure.build_not_found_error(message="Môn học không tồn tại")
                except ValidationError as e:
                    errs = e.errors()
                    raise HTTPException(status_code=422, detail=errs)
                if req_object.payload.type == FormType.SUBJECT_ABSENT:
                    if subject.status == StatusSubjectEnum.INIT:
                        self.subject_repository.update(
                            id=subject.id,
                            data={
                                "status": StatusSubjectEnum.SENT_NOTIFICATION,
                                "updated_at": datetime.now(timezone.utc),
                            },
                        )
                else:
                    if subject.status != StatusSubjectEnum.SENT_EVALUATION:
                        self.subject_repository.update(
                            id=subject.id,
                            data={
                                "status": StatusSubjectEnum.SENT_EVALUATION,
                                "updated_at": datetime.now(timezone.utc),
                            },
                        )

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
                    description=json.dumps(
                        req_object.payload.model_dump(exclude_none=True), default=str, ensure_ascii=False
                    ),
                ),
            )
            return ManageFormInDB.model_validate(doc)
