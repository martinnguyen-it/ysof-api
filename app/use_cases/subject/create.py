import json
from typing import Optional
from fastapi import Depends, BackgroundTasks

from app.models.subject import SubjectModel
from app.shared import request_object, use_case, response_object

from app.domain.subject.entity import Subject, SubjectInCreate, SubjectInDB
from app.infra.subject.subject_repository import SubjectRepository
from app.domain.lecturer.entity import Lecturer, LecturerInDB
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.models.lecturer import LecturerModel
from app.models.admin import AdminModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.shared.utils.general import get_current_season_value


class CreateSubjectRequestObject(request_object.ValidRequestObject):
    def __init__(self, current_admin: AdminModel, subject_in: SubjectInCreate) -> None:
        self.subject_in = subject_in
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls, current_admin: AdminModel, payload: Optional[SubjectInCreate] = None
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return CreateSubjectRequestObject(subject_in=payload, current_admin=current_admin)


class CreateSubjectUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        lecturer_repository: LecturerRepository = Depends(LecturerRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.subject_repository = subject_repository
        self.lecturer_repository = lecturer_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: CreateSubjectRequestObject):
        lecturer: Optional[LecturerModel] = self.lecturer_repository.get_by_id(req_object.subject_in.lecturer)
        if not lecturer:
            return response_object.ResponseFailure.build_not_found_error("Giảng viên không tồn tại")

        current_season = get_current_season_value()

        obj_in: SubjectInDB = SubjectInDB(
            **req_object.subject_in.model_dump(exclude={"lecturer"}),
            lecturer=lecturer,
            season=current_season,
        )
        subject: SubjectModel = self.subject_repository.create(subject=obj_in)

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
                    req_object.subject_in.model_dump(exclude_none=True), default=str, ensure_ascii=False
                ),
            ),
        )

        return Subject(
            **SubjectInDB.model_validate(subject).model_dump(exclude=({"lecturer"})),
            lecturer=Lecturer(**LecturerInDB.model_validate(subject.lecturer).model_dump()),
        )
