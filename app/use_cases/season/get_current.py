from fastapi import Depends
import json
from typing import Optional
from app.shared import response_object, use_case
from app.domain.season.entity import Season, SeasonInDB
from app.infra.season.season_repository import SeasonRepository
from app.models.season import SeasonModel
from app.shared.utils.general import cache


class GetCurrentSeasonCase(use_case.UseCase):
    def __init__(self, season_repository: SeasonRepository = Depends(SeasonRepository)):
        self.season_repository = season_repository

    def process_request(self):
        if "season-detail" not in cache:
            season: Optional[SeasonModel] = self.season_repository.get_current_season()
            if not season:
                return response_object.ResponseFailure.build_not_found_error(
                    message="Không tồn tại"
                )

            cache["season-detail"] = json.dumps(
                Season(**SeasonInDB.model_validate(season).model_dump()).model_dump(), default=str
            )
        return Season(**json.loads(cache["season-detail"]))
