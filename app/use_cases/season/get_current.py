from fastapi import Depends
import json
from typing import Optional
from app.shared import response_object, use_case
from app.domain.season.entity import Season, SeasonInDB
from app.infra.season.season_repository import SeasonRepository
from app.models.season import SeasonModel
from app.config.redis import RedisDependency
from app.shared.utils.general import TTL_30_DAYS


class GetCurrentSeasonCase(use_case.UseCase):
    def __init__(
        self,
        redis_client: RedisDependency,
        season_repository: SeasonRepository = Depends(SeasonRepository),
    ):
        self.season_repository = season_repository
        self.redis_client = redis_client

    def process_request(self):
        if not self.redis_client.exists("season-detail"):
            season: Optional[SeasonModel] = self.season_repository.get_current_season()
            if not season:
                return response_object.ResponseFailure.build_not_found_error(
                    message="Không tồn tại"
                )

            cache_data = json.dumps(
                Season(**SeasonInDB.model_validate(season).model_dump()).model_dump(), default=str
            )
            self.redis_client.setex(
                "season-detail", TTL_30_DAYS, cache_data
            )  # Cache 1 item for 30 days
        return Season(**json.loads(self.redis_client.get("season-detail")))
