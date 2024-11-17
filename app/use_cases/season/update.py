from typing import Optional
from fastapi import Depends
from app.models.season import SeasonModel
from app.shared import request_object, use_case, response_object

from app.domain.season.entity import Season, SeasonInDB, SeasonInUpdate, SeasonInUpdateTime
from app.infra.season.season_repository import SeasonRepository


class UpdateSeasonRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str, obj_in: SeasonInUpdate) -> None:
        self.id = id
        self.obj_in = obj_in

    @classmethod
    def builder(
        cls, id: str, payload: Optional[SeasonInUpdate] = None
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid id")

        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateSeasonRequestObject(id=id, obj_in=payload)


class UpdateSeasonUseCase(use_case.UseCase):
    def __init__(self, season_repository: SeasonRepository = Depends(SeasonRepository)):
        self.season_repository = season_repository

    def process_request(self, req_object: UpdateSeasonRequestObject):
        season: Optional[SeasonModel] = self.season_repository.get_by_id(req_object.id)
        if not season:
            return response_object.ResponseFailure.build_not_found_error("Năm học không tồn tại")

        self.season_repository.update(
            id=season.id, data=SeasonInUpdateTime(**req_object.obj_in.model_dump())
        )
        season.reload()

        return Season(**SeasonInDB.model_validate(season).model_dump())
