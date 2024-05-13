from fastapi import Depends, BackgroundTasks
import json
from typing import Optional
from app.shared import request_object, response_object, use_case
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel
from app.infra.tasks.email import send_email_notification_subject_task
from app.domain.subject.entity import SubjectInUpdateTime
from app.domain.subject.enum import StatusSubjectEnum
from app.infra.manage_form.manage_form_repository import ManageFormRepository
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.models.manage_form import ManageFormModel
from app.domain.manage_form.entity import ManageFormInDB, ManageFormUpdateWithTime
from app.domain.manage_form.enum import FormStatus, FormType
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.shared.utils.general import get_current_season_value
from app.models.admin import AdminModel


class SubjectSendNotificationRequestObject(request_object.ValidRequestObject):
    def __init__(self, subject_id: str, current_admin: AdminModel):
        self.subject_id = subject_id
        self.current_admin = current_admin

    @classmethod
    def builder(cls, subject_id: str, current_admin: AdminModel) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not id:
            invalid_req.add_error("id", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return SubjectSendNotificationRequestObject(subject_id=subject_id, current_admin=current_admin)


class SubjectSendNotificationUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        manage_form_repository: ManageFormRepository = Depends(ManageFormRepository),
    ):
        self.subject_repository = subject_repository
        self.manage_form_repository = manage_form_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: SubjectSendNotificationRequestObject):
        subject: Optional[SubjectModel] = self.subject_repository.get_by_id(subject_id=req_object.subject_id)
        manage_form: ManageFormModel | None = self.manage_form_repository.find_one(
            {"type": FormType.SUBJECT_EVALUATION}
        )

        if not subject:
            return response_object.ResponseFailure.build_not_found_error(message="Môn học không tồn tại")
        res = self.subject_repository.update(
            subject.id, data=SubjectInUpdateTime(status=StatusSubjectEnum.SENT_STUDENT)
        )

        if manage_form:
            self.manage_form_repository.update(
                id=manage_form.id,
                data=ManageFormUpdateWithTime(
                    data=dict(subject_id=req_object.subject_id),
                    status=FormStatus.INACTIVE,
                    type=FormType.SUBJECT_EVALUATION,
                ),
            )
        else:
            self.manage_form_repository.create(
                ManageFormInDB(
                    data=dict(subject_id=req_object.subject_id),
                    status=FormStatus.INACTIVE,
                    type=FormType.SUBJECT_EVALUATION,
                )
            )

        current_season = get_current_season_value()
        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.CREATE,
                endpoint=Endpoint.SUBJECT,
                season=current_season,
                author=req_object.current_admin,
                author_email=req_object.current_admin.email,
                author_name=req_object.current_admin.full_name,
                author_roles=req_object.current_admin.roles,
                description=json.dumps(
                    {"name": "Send email notification", "subject_id": req_object.subject_id, "subject": subject.title},
                    default=str,
                    ensure_ascii=False,
                ),
            ),
        )

        if res:
            send_email_notification_subject_task.delay(subject_id=req_object.subject_id)
            return True
        else:
            return response_object.ResponseFailure.build_system_error("Something went wrong")
