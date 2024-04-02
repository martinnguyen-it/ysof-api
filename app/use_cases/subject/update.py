from typing import Optional
from fastapi import Depends
from app.models.subject import SubjectModel
from app.shared import request_object, use_case, response_object

from app.domain.subject.entity import (Subject, SubjectInDB, SubjectInUpdate,
                                       SubjectInUpdateTime)
from app.infra.subject.subject_repository import SubjectRepository
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.models.lecturer import LecturerModel
from app.domain.lecturer.entity import Lecturer, LecturerInDB
from app.models.admin import AdminModel
from app.infra.season.season_repository import SeasonRepository
from app.models.season import SeasonModel
from app.shared.constant import SUPER_ADMIN
from app.shared.common_exception import forbidden_exception


class UpdateSubjectRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str, current_admin: AdminModel,
                 obj_in: SubjectInUpdate) -> None:
        self.id = id
        self.obj_in = obj_in
        self.current_admin = current_admin

    @classmethod
    def builder(cls, id: str, current_admin: AdminModel,
                payload: Optional[SubjectInUpdate] = None
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
    def __init__(self,
                 lecturer_repository: LecturerRepository = Depends(
                     LecturerRepository),
                 subject_repository: SubjectRepository = Depends(
                     SubjectRepository),
                 season_repository: SeasonRepository = Depends(SeasonRepository)):
        self.lecturer_repository = lecturer_repository
        self.subject_repository = subject_repository
        self.season_repository = season_repository

    def process_request(self, req_object: UpdateSubjectRequestObject):
        subject: Optional[SubjectModel] = self.subject_repository.get_by_id(
            req_object.id)
        if not subject:
            return response_object.ResponseFailure.build_not_found_error("Môn học không tồn tại")

        current_season: SeasonModel = self.season_repository.get_current_season()
        if subject.season != current_season.season and \
                not any(role in req_object.current_admin.roles for role in SUPER_ADMIN):
            raise forbidden_exception

        lecturer: Optional[LecturerModel] = None
        if isinstance(req_object.obj_in.lecturer, str):
            lecturer: Optional[LecturerModel] = self.lecturer_repository.get_by_id(
                req_object.obj_in.lecturer)
            if not lecturer:
                return response_object.ResponseFailure.build_not_found_error("Giảng viên không tồn tại")

        self.subject_repository.update(id=subject.id, data=SubjectInUpdateTime(
            **req_object.obj_in.model_dump(exclude=())) if lecturer is None
            else SubjectInUpdateTime(**req_object.obj_in.model_dump(exclude={"lecturer"}),
                                     lecturer=lecturer)
        )
        subject.reload()

        return Subject(**SubjectInDB.model_validate(subject).model_dump(exclude=({"lecturer"})),
                       lecturer=Lecturer(**LecturerInDB.model_validate(subject.lecturer).model_dump()))
