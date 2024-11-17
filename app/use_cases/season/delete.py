from typing import Optional

from fastapi import Depends
from app.infra.season.season_repository import SeasonRepository
from app.shared import request_object, response_object, use_case
from app.models.season import SeasonModel


class DeleteSeasonRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str):
        self.id = id

    @classmethod
    def builder(cls, id: str) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid id")

        if invalid_req.has_errors():
            return invalid_req

        return DeleteSeasonRequestObject(id=id)


class DeleteSeasonUseCase(use_case.UseCase):
    def __init__(self, season_repository: SeasonRepository = Depends(SeasonRepository)):
        self.season_repository = season_repository

    def process_request(self, req_object: DeleteSeasonRequestObject):
        season: Optional[SeasonModel] = self.season_repository.get_by_id(req_object.id)
        if not season:
            return response_object.ResponseFailure.build_not_found_error("Năm học không tồn tại")
        if season.is_current is True:
            return response_object.ResponseFailure.build_parameters_error(
                "Không thể xóa mùa đang hoạt động"
            )

        try:
            self.season_repository.delete(id=season.id)
            return {"success": True}
        except Exception:
            return response_object.ResponseFailure.build_system_error("Something went error.")
