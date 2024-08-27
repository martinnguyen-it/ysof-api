from typing import Optional, List
from fastapi import Depends
from app.shared import request_object, use_case
from app.domain.season.entity import Season, SeasonInDB
from app.models.season import SeasonModel
from app.infra.season.season_repository import SeasonRepository


class ListSeasonsRequestObject(request_object.ValidRequestObject):
    def __init__(
        self, page_index: int | None = None, page_size: int | None = None, sort: Optional[dict[str, int]] = None
    ):
        self.sort = sort
        self.page_index = page_index
        self.page_size = page_size

    @classmethod
    def builder(
        cls, page_index: int | None = None, page_size: int | None = None, sort: Optional[dict[str, int]] = None
    ):
        return ListSeasonsRequestObject(sort=sort, page_index=page_index, page_size=page_size)


class ListSeasonsUseCase(use_case.UseCase):
    def __init__(self, season_repository: SeasonRepository = Depends(SeasonRepository)):
        self.season_repository = season_repository

    def process_request(self, req_object: ListSeasonsRequestObject):

        seasons: List[SeasonModel] = self.season_repository.list(sort=req_object.sort)

        return [Season(**SeasonInDB.model_validate(season).model_dump()) for season in seasons]
