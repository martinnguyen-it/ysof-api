from typing import Optional
from fastapi import Depends

from app.models.season import SeasonModel
from app.shared import request_object, use_case, response_object

from app.domain.season.entity import Season, SeasonInCreate, SeasonInDB
from app.infra.season.season_repository import SeasonRepository
from app.shared.utils.general import clear_all_cache


class CreateSeasonRequestObject(request_object.ValidRequestObject):
    def __init__(self, season_in: SeasonInCreate) -> None:
        self.season_in = season_in

    @classmethod
    def builder(cls, payload: Optional[SeasonInCreate] = None) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return CreateSeasonRequestObject(season_in=payload)


class CreateSeasonUseCase(use_case.UseCase):
    def __init__(self, season_repository: SeasonRepository = Depends(SeasonRepository)):
        self.season_repository = season_repository

    def process_request(self, req_object: CreateSeasonRequestObject):
        existing_season: SeasonModel = self.season_repository.find_one({"season": req_object.season_in.season})
        if existing_season:
            return response_object.ResponseFailure.build_parameters_error(message="Năm học đã tồn tại")
        clear_all_cache()
        current_seasons: list[SeasonModel] = self.season_repository.list(
            match_pipeline={"$match": {"is_current": True}}
        )
        if len(current_seasons) > 0:
            self.season_repository.bulk_update(data={"is_current": False}, entities=current_seasons)

        obj_in: SeasonInDB = SeasonInDB(
            **req_object.season_in.model_dump(),
            is_current=True,
        )
        season: SeasonModel = self.season_repository.create(season=obj_in)

        return Season(**SeasonInDB.model_validate(season).model_dump())
