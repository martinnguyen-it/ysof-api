from typing import Optional

from fastapi import Depends
from app.infra.subject.subject_repository import SubjectRepository
from app.shared import request_object, response_object, use_case
from app.models.subject import SubjectModel
from app.models.admin import AdminModel
from app.infra.season.season_repository import SeasonRepository
from app.models.season import SeasonModel
from app.shared.constant import SUPER_ADMIN
from app.shared.common_exception import forbidden_exception


class DeleteSubjectRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str, current_admin: AdminModel):
        self.id = id
        self.current_admin = current_admin

    @classmethod
    def builder(cls, id: str, current_admin: AdminModel) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid id")

        if invalid_req.has_errors():
            return invalid_req

        return DeleteSubjectRequestObject(id=id, current_admin=current_admin)


class DeleteSubjectUseCase(use_case.UseCase):
    def __init__(self,
                 subject_repository: SubjectRepository = Depends(
                     SubjectRepository),
                 season_repository: SeasonRepository = Depends(SeasonRepository)):
        self.subject_repository = subject_repository
        self.season_repository = season_repository

    def process_request(self, req_object: DeleteSubjectRequestObject):
        subject: Optional[SubjectModel] = self.subject_repository.get_by_id(
            req_object.id)
        if not subject:
            return response_object.ResponseFailure.build_not_found_error("Môn học không tồn tại")

        current_season: SeasonModel = self.season_repository.get_current_season()
        if subject.season != current_season.season and \
                not any(role in req_object.current_admin.roles for role in SUPER_ADMIN):
            raise forbidden_exception

        try:
            self.subject_repository.delete(id=subject.id)
            return {"success": True}
        except Exception:
            return response_object.ResponseFailure.build_system_error("Something went error.")
