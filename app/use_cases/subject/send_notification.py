from fastapi import Depends, BackgroundTasks
import json
from typing import Optional
from app.infra.tasks.email import (
    send_email_notification_subject_task_for_extra_mails,
    send_email_notification_subject_task,
)
from app.shared import request_object, response_object, use_case
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel
from app.domain.subject.entity import SubjectInUpdateTime
from app.domain.subject.enum import StatusSubjectEnum
from app.infra.manage_form.manage_form_repository import ManageFormRepository
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.models.manage_form import ManageFormModel
from app.domain.manage_form.entity import ManageFormInDB, ManageFormUpdateWithTime
from app.domain.manage_form.enum import FormStatus, FormType
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.shared.utils.general import (
    get_current_season_value,
    TTL_5_DAYS,
    get_subject_extra_emails_redis_key,
)
from app.models.admin import AdminModel
from app.config.redis import RedisDependency


class SubjectSendNotificationRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        subject_id: str,
        current_admin: AdminModel,
        extra_emails: Optional[set[str]] = None,
    ):
        self.subject_id = subject_id
        self.current_admin = current_admin
        self.extra_emails = extra_emails

    @classmethod
    def builder(
        cls,
        subject_id: str,
        current_admin: AdminModel,
        extra_emails: Optional[set[str]] = None,
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not subject_id:
            invalid_req.add_error("subject_id", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return SubjectSendNotificationRequestObject(
            subject_id=subject_id, current_admin=current_admin, extra_emails=extra_emails
        )


class SubjectSendNotificationUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        redis_client: RedisDependency,
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        manage_form_repository: ManageFormRepository = Depends(ManageFormRepository),
    ):
        self.subject_repository = subject_repository
        self.manage_form_repository = manage_form_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository
        self.redis_client = redis_client

    def process_request(self, req_object: SubjectSendNotificationRequestObject):
        subject: Optional[SubjectModel] = self.subject_repository.get_by_id(
            subject_id=req_object.subject_id
        )

        if not subject:
            return response_object.ResponseFailure.build_not_found_error(
                message="Môn học không tồn tại"
            )

        if not subject.zoom.link or not subject.zoom.meeting_id or not subject.zoom.pass_code:
            return response_object.ResponseFailure.build_parameters_error(
                message="Môn học chưa có thông tin zoom."
            )

        # Get Redis key for this subject's extra emails
        redis_key = get_subject_extra_emails_redis_key(req_object.subject_id)
        existing_extra_emails = (
            self.redis_client.smembers(redis_key) if self.redis_client.exists(redis_key) else set()
        )

        # Check if this is a repeat notification with extra_emails
        if subject.status == StatusSubjectEnum.SENT_NOTIFICATION:
            # This is a repeat notification - only send emails to extra addresses
            # Update the extra emails set in Redis (union with existing)
            all_extra_emails = existing_extra_emails.union(req_object.extra_emails)
            self.redis_client.delete(redis_key)  # Clear existing
            for email in all_extra_emails:
                self.redis_client.sadd(redis_key, email)
            self.redis_client.expire(redis_key, TTL_5_DAYS)

            # Only send emails to extra addresses, skip main subject logic
            if req_object.extra_emails:
                send_email_notification_subject_task_for_extra_mails.delay(
                    subject_id=req_object.subject_id, emails=list(req_object.extra_emails)
                )

            # Log the action
            current_season = get_current_season_value()
            self.background_tasks.add_task(
                self.audit_log_repository.create,
                AuditLogInDB(
                    type=AuditLogType.OTHER,
                    endpoint=Endpoint.SUBJECT,
                    season=current_season,
                    author=req_object.current_admin,
                    author_email=req_object.current_admin.email,
                    author_name=req_object.current_admin.full_name,
                    author_roles=req_object.current_admin.roles,
                    description=json.dumps(
                        {
                            "name": "Send email notification to extra emails (repeat)",
                            "subject_id": req_object.subject_id,
                            "subject": subject.title,
                            "extra_emails": (
                                list(req_object.extra_emails) if req_object.extra_emails else []
                            ),
                        },
                        default=str,
                        ensure_ascii=False,
                    ),
                ),
            )
            return True

        # First time notification or no extra emails in Redis - run full logic
        manage_form: ManageFormModel | None = self.manage_form_repository.find_one(
            {"type": FormType.SUBJECT_EVALUATION}
        )

        res = self.subject_repository.update(
            subject.id, data=SubjectInUpdateTime(status=StatusSubjectEnum.SENT_NOTIFICATION)
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

        # Store extra emails in Redis if provided
        if req_object.extra_emails:
            for email in req_object.extra_emails:
                self.redis_client.sadd(redis_key, email)
            self.redis_client.expire(redis_key, TTL_5_DAYS)

        # Log the action
        current_season = get_current_season_value()
        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.OTHER,
                endpoint=Endpoint.SUBJECT,
                season=current_season,
                author=req_object.current_admin,
                author_email=req_object.current_admin.email,
                author_name=req_object.current_admin.full_name,
                author_roles=req_object.current_admin.roles,
                description=json.dumps(
                    {
                        "name": "Send email notification",
                        "subject_id": req_object.subject_id,
                        "subject": subject.title,
                        "extra_emails": (
                            list(req_object.extra_emails) if req_object.extra_emails else []
                        ),
                    },
                    default=str,
                    ensure_ascii=False,
                ),
            ),
        )

        if res:
            # Send main notification
            send_email_notification_subject_task.delay(subject_id=req_object.subject_id)

            # Send to extra emails if provided
            if req_object.extra_emails and len(req_object.extra_emails) > 0:
                send_email_notification_subject_task_for_extra_mails.delay(
                    subject_id=req_object.subject_id, emails=list(req_object.extra_emails)
                )

            return True
        else:
            return response_object.ResponseFailure.build_system_error("Something went wrong")
