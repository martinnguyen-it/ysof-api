from typing import Optional
from fastapi import Depends, HTTPException
from app.models.season import SeasonModel
from app.shared import request_object, use_case, response_object

from app.domain.season.entity import Season, SeasonInDB, SeasonInUpdateTime
from app.infra.season.season_repository import SeasonRepository
from app.shared.utils.general import clear_all_cache
from pymongo.errors import PyMongoError
from mongoengine.connection import get_connection


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
        season: Optional[SeasonModel] = self.season_repository.get_by_id(req_object.id)
        if not season:
            return response_object.ResponseFailure.build_not_found_error("Năm học không tồn tại")

        client = get_connection()
        with client.start_session() as session:
            with session.start_transaction():
                try:
                    clear_all_cache()
                    current_seasons: list[SeasonModel] = self.season_repository.list(
                        match_pipeline={"$match": {"is_current": True}}
                    )
                    if len(current_seasons) > 0:
                        self.season_repository.bulk_update(
                            data={"is_current": False}, entities=current_seasons, session=session
                        )

                    self.season_repository.update(
                        id=season.id, data=SeasonInUpdateTime(is_current=True)
                    )
                    season.reload()

                    session.commit_transaction()
                    return Season(**SeasonInDB.model_validate(season).model_dump())
                except (PyMongoError, ValueError):
                    session.abort_transaction()
                    raise HTTPException(status_code=400, detail=str("Something went wrong"))
                except Exception:
                    session.abort_transaction()
                    raise HTTPException(status_code=400, detail=str("Something went wrong"))
                finally:
                    session.end_session()
