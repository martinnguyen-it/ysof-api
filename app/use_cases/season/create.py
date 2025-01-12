from typing import Optional
from fastapi import Depends, HTTPException

from app.models.season import SeasonModel
from app.shared import request_object, use_case, response_object

from app.domain.season.entity import Season, SeasonInCreate, SeasonInDB
from app.infra.season.season_repository import SeasonRepository
from app.shared.utils.general import clear_all_cache
from mongoengine.connection import get_connection

from pymongo.errors import PyMongoError
from mongoengine import NotUniqueError


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
        client = get_connection()
        with client.start_session() as session:
            with session.start_transaction():
                try:
                    current_seasons: list[SeasonModel] = self.season_repository.list(
                        match_pipeline={"$match": {"is_current": True}}
                    )

                    if len(current_seasons) > 0:
                        self.season_repository.bulk_update(
                            data={"is_current": False}, entities=current_seasons, session=session
                        )
                    clear_all_cache()

                    obj_in: SeasonInDB = SeasonInDB(
                        **req_object.season_in.model_dump(),
                        is_current=True,
                    )

                    season: SeasonModel = self.season_repository.create(
                        season=obj_in, session=session
                    )

                    # Commit the transaction
                    session.commit_transaction()
                    return Season(**SeasonInDB.model_validate(season).model_dump())

                except NotUniqueError:
                    session.abort_transaction()
                    return response_object.ResponseFailure.build_parameters_error(
                        message="Năm học đã tồn tại"
                    )

                except (PyMongoError, ValueError):
                    session.abort_transaction()
                    raise HTTPException(status_code=400, detail=str("Something went wrong"))
                except Exception:
                    session.abort_transaction()
                    raise HTTPException(status_code=400, detail=str("Something went wrong"))
                finally:
                    session.end_session()
