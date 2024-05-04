from typing import Optional
from fastapi import Depends
from app.models.season import SeasonModel
from app.shared import request_object, use_case, response_object

from app.domain.season.entity import Season, SeasonInDB, SeasonInUpdateTime
from app.infra.season.season_repository import SeasonRepository
from app.shared.utils.general import clear_all_cache


class MarkCurrentSeasonRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str) -> None:
        self.id = id

    @classmethod
    def builder(cls, id: str) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid id")

        return MarkCurrentSeasonRequestObject(id=id)


class MarkCurrentSeasonUseCase(use_case.UseCase):
    def __init__(self, season_repository: SeasonRepository = Depends(SeasonRepository)):
        self.season_repository = season_repository

    def process_request(self, req_object: MarkCurrentSeasonRequestObject):
        clear_all_cache()
        season: Optional[SeasonModel] = self.season_repository.get_by_id(req_object.id)
        if not season:
            return response_object.ResponseFailure.build_not_found_error("Năm học không tồn tại")

        current_seasons: list[SeasonModel] = self.season_repository.list(
            match_pipeline={"$match": {"is_current": True}}
        )
        if len(current_seasons) > 0:
            self.season_repository.bulk_update(data={"is_current": False}, entities=current_seasons)

        self.season_repository.update(id=season.id, data=SeasonInUpdateTime(is_current=True))
        season.reload()

        return Season(**SeasonInDB.model_validate(season).model_dump())
