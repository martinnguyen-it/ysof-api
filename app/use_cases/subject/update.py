import json
from typing import Optional
from fastapi import Depends, BackgroundTasks
from app.models.subject import SubjectModel
from app.shared import request_object, use_case, response_object

from app.domain.subject.entity import Subject, SubjectInDB, SubjectInUpdate, SubjectInUpdateTime
from app.infra.subject.subject_repository import SubjectRepository
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.models.lecturer import LecturerModel
from app.domain.lecturer.entity import Lecturer, LecturerInDB
from app.models.admin import AdminModel
from app.shared.constant import SUPER_ADMIN
from app.shared.common_exception import forbidden_exception
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.shared.utils.general import get_current_season_value
from app.domain.document.entity import AdminInDocument, Document, DocumentInDB
from app.domain.admin.entity import AdminInDB
from app.domain.document.enum import DocumentType
from app.infra.document.document_repository import DocumentRepository


class UpdateSubjectRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str, current_admin: AdminModel, obj_in: SubjectInUpdate) -> None:
        self.id = id
        self.obj_in = obj_in
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls, id: str, current_admin: AdminModel, payload: Optional[SubjectInUpdate] = None
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid client id")

        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateSubjectRequestObject(id=id, obj_in=payload, current_admin=current_admin)


class UpdateSubjectUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        lecturer_repository: LecturerRepository = Depends(LecturerRepository),
        document_repository: DocumentRepository = Depends(DocumentRepository),
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.lecturer_repository = lecturer_repository
        self.subject_repository = subject_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository
        self.document_repository = document_repository

    def process_request(self, req_object: UpdateSubjectRequestObject):
        subject: Optional[SubjectModel] = self.subject_repository.get_by_id(req_object.id)
        if not subject:
            return response_object.ResponseFailure.build_not_found_error("Môn học không tồn tại")

        current_season = get_current_season_value()

        attachments: list | None = None
        if isinstance(req_object.obj_in.attachments, list):
            attachments = []
            for doc_id in req_object.obj_in.attachments:
                doc = self.document_repository.get_by_id(doc_id)
                if doc is None or doc.season != current_season:
                    return response_object.ResponseFailure.build_not_found_error(
                        message="Tài liệu đính kèm không tồn tại hoặc thuộc mùa cũ"
                    )
                if doc.type != DocumentType.STUDENT:
                    return response_object.ResponseFailure.build_parameters_error(
                        message="Vui lòng chỉ chọn tài liệu đính kèm dành cho học viên"
                    )
                attachments.append(doc)

        if subject.season != current_season and not any(role in req_object.current_admin.roles for role in SUPER_ADMIN):
            raise forbidden_exception

        lecturer: Optional[LecturerModel] = None
        if isinstance(req_object.obj_in.lecturer, str):
            lecturer: Optional[LecturerModel] = self.lecturer_repository.get_by_id(req_object.obj_in.lecturer)
            if not lecturer:
                return response_object.ResponseFailure.build_not_found_error("Giảng viên không tồn tại")

        self.subject_repository.update(
            id=subject.id,
            data=(
                SubjectInUpdateTime(
                    **req_object.obj_in.model_dump(exclude=("lecturer", "attachments")),
                    lecturer=lecturer,
                    attachments=attachments,
                )
            ),
        )
        subject.reload()

        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.UPDATE,
                endpoint=Endpoint.SUBJECT,
                season=current_season,
                author=req_object.current_admin,
                author_email=req_object.current_admin.email,
                author_name=req_object.current_admin.full_name,
                author_roles=req_object.current_admin.roles,
                description=json.dumps(
                    req_object.obj_in.model_dump(exclude_none=True), default=str, ensure_ascii=False
                ),
            ),
        )

        return Subject(
            **SubjectInDB.model_validate(subject).model_dump(exclude=({"lecturer", "attachments"})),
            lecturer=Lecturer(**LecturerInDB.model_validate(subject.lecturer).model_dump()),
            attachments=[
                Document(
                    **DocumentInDB.model_validate(doc).model_dump(exclude=({"author"})),
                    author=AdminInDocument(**AdminInDB.model_validate(doc.author).model_dump()),
                )
                for doc in subject.attachments
            ],
        )
