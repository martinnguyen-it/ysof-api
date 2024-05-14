import json
from typing import Optional
from fastapi import Depends, BackgroundTasks

from app.shared import request_object, use_case, response_object

from app.models.admin import AdminModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.shared.utils.general import get_current_season_value
from app.domain.subject.subject_evaluation.entity import (
    SubjectEvaluationQuestion,
    SubjectEvaluationQuestionInCreate,
    SubjectEvaluationQuestionInDB,
)
from app.infra.subject.subject_evaluation_question_repository import SubjectEvaluationQuestionRepository
from app.models.subject_evaluation import SubjectEvaluationQuestionModel
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel


class CreateSubjectEvaluationQuestionRequestObject(request_object.ValidRequestObject):
    def __init__(self, current_admin: AdminModel, obj_in: SubjectEvaluationQuestionInCreate, subject_id=str) -> None:
        self.obj_in = obj_in
        self.current_admin = current_admin
        self.subject_id = subject_id

    @classmethod
    def builder(
        cls, current_admin: AdminModel, subject_id: str, payload: Optional[SubjectEvaluationQuestionInCreate] = None
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return CreateSubjectEvaluationQuestionRequestObject(
            obj_in=payload, current_admin=current_admin, subject_id=subject_id
        )


class CreateSubjectEvaluationQuestionUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        subject_evaluation_question_repository: SubjectEvaluationQuestionRepository = Depends(
            SubjectEvaluationQuestionRepository
        ),
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.subject_repository = subject_repository
        self.subject_evaluation_question_repository = subject_evaluation_question_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: CreateSubjectEvaluationQuestionRequestObject):
        subject: Optional[SubjectModel] = self.subject_repository.get_by_id(req_object.subject_id)
        if not subject:
            return response_object.ResponseFailure.build_not_found_error("Môn học không tồn tại")

        obj_in: SubjectEvaluationQuestionInDB = SubjectEvaluationQuestionInDB(
            **req_object.obj_in.model_dump(),
            subject=subject,
        )

        existed: SubjectEvaluationQuestionModel | None = self.subject_evaluation_question_repository.get_by_subject_id(
            subject_id=req_object.subject_id
        )
        if existed:
            self.subject_evaluation_question_repository.delete(id=existed.id)

        subject_evaluation_question: SubjectEvaluationQuestionModel = (
            self.subject_evaluation_question_repository.create(doc=obj_in)
        )

        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.CREATE,
                endpoint=Endpoint.SUBJECT_EVALUATION_QUESTION,
                season=get_current_season_value(),
                author=req_object.current_admin,
                author_email=req_object.current_admin.email,
                author_name=req_object.current_admin.full_name,
                author_roles=req_object.current_admin.roles,
                description=json.dumps(
                    req_object.obj_in.model_dump(exclude_none=True), default=str, ensure_ascii=False
                ),
            ),
        )

        return SubjectEvaluationQuestion(
            **SubjectEvaluationQuestionInDB.model_validate(subject_evaluation_question).model_dump(
                exclude=({"subject"})
            ),
        )
