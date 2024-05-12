from fastapi import Depends
from typing import Optional
from app.shared import request_object, response_object, use_case
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel
from app.infra.tasks.email import send_email_notification_subject_task
from app.domain.subject.entity import SubjectInUpdateTime
from app.domain.subject.enum import StatusSubjectEnum


class SubjectSendNotificationRequestObject(request_object.ValidRequestObject):
    def __init__(self, subject_id: str):
        self.subject_id = subject_id

    @classmethod
    def builder(cls, subject_id: str) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not id:
            invalid_req.add_error("id", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return SubjectSendNotificationRequestObject(subject_id=subject_id)


class SubjectSendNotificationUseCase(use_case.UseCase):
    def __init__(self, subject_repository: SubjectRepository = Depends(SubjectRepository)):
        self.subject_repository = subject_repository

    def process_request(self, req_object: SubjectSendNotificationRequestObject):
        subject: Optional[SubjectModel] = self.subject_repository.get_by_id(subject_id=req_object.subject_id)
        if not subject:
            return response_object.ResponseFailure.build_not_found_error(message="Môn học không tồn tại")
        res = self.subject_repository.update(
            subject.id, data=SubjectInUpdateTime(status=StatusSubjectEnum.SENT_STUDENT)
        )

        if res:
            send_email_notification_subject_task.delay(subject_id=req_object.subject_id)
            return True
        else:
            return response_object.ResponseFailure.build_system_error("Something went wrong")
