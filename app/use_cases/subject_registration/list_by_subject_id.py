from fastapi import Depends
from typing import Optional
from app.domain.shared.enum import AdminRole
from app.models.admin import AdminModel
from app.shared import request_object, use_case, response_object
from app.infra.subject.subject_registration_repository import SubjectRegistrationRepository
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel
from app.domain.subject.entity import StudentInSubject
from app.domain.student.entity import StudentInDB
from app.models.subject_registration import SubjectRegistrationModel


class ListSubjectRegistrationsBySubjectIdRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        current_admin: AdminModel,
        subject_id: str,
    ):
        self.subject_id = subject_id
        self.current_admin = current_admin

    @classmethod
    def builder(cls, current_admin: AdminModel, subject_id: str):
        return ListSubjectRegistrationsBySubjectIdRequestObject(
            subject_id=subject_id,
            current_admin=current_admin,
        )


class ListSubjectRegistrationsBySubjectIdUseCase(use_case.UseCase):
    def __init__(
        self,
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        subject_registration_repository: SubjectRegistrationRepository = Depends(
            SubjectRegistrationRepository
        ),
    ):
        self.subject_repository = subject_repository
        self.subject_registration_repository = subject_registration_repository

    def process_request(self, req_object: ListSubjectRegistrationsBySubjectIdRequestObject):
        subject: Optional[SubjectModel] = self.subject_repository.get_by_id(
            subject_id=req_object.subject_id
        )

        if not subject:
            return response_object.ResponseFailure.build_not_found_error(
                message="Môn học không tồn tại"
            )

        if not (
            subject.season <= req_object.current_admin.latest_season
            or AdminRole.ADMIN in req_object.current_admin.roles
        ):
            return response_object.ResponseFailure.build_parameters_error(
                f"Bạn không có quyền truy cập môn học thuộc mùa {subject.season}"
            )

        docs: list[SubjectRegistrationModel] = (
            self.subject_registration_repository.get_by_subject_id(subject_id=subject.id)
        )

        return [
            StudentInSubject(**StudentInDB.model_validate(doc.student).model_dump()) for doc in docs
        ]
