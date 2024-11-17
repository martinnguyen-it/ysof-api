from fastapi import Depends
from typing import Optional
from app.shared import request_object, response_object, use_case
from app.domain.season.entity import Season, SeasonInDB
from app.infra.season.season_repository import SeasonRepository
from app.models.season import SeasonModel


class GetSeasonRequestObject(request_object.ValidRequestObject):
    def __init__(self, season_id: str):
        self.season_id = season_id

    @classmethod
    def builder(cls, season_id: str) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not id:
            invalid_req.add_error("id", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return GetSeasonRequestObject(season_id=season_id)


class GetSeasonCase(use_case.UseCase):
    def __init__(self, season_repository: SeasonRepository = Depends(SeasonRepository)):
        self.season_repository = season_repository

    def process_request(self, req_object: GetSeasonRequestObject):
        season: Optional[SeasonModel] = self.season_repository.get_by_id(
            season_id=req_object.season_id
        )
        if not season:
            return response_object.ResponseFailure.build_not_found_error(
                message="Năm học không tồn tại"
            )

        return Season(**SeasonInDB.model_validate(season).model_dump())
