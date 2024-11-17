"""Season repository module"""

from typing import Optional, Dict, Union, List, Any
from mongoengine import QuerySet, DoesNotExist
from bson import ObjectId
import pymongo
from fastapi import HTTPException

from app.models.season import SeasonModel
from app.domain.season.entity import SeasonInDB, SeasonInUpdate, SeasonInUpdateTime


class SeasonRepository:
    def __init__(self):
        pass

    def create(self, season: SeasonInDB) -> SeasonModel:
        """
        Create new season in db
        :param season:
        :return:
        """
        # create season instance
        new_doc = SeasonModel(**season.model_dump()).save()
        # and save it to db
        return new_doc

    def get_by_id(self, season_id: Union[str, ObjectId]) -> Optional[SeasonModel]:
        """
        Get season in db from id
        :param season_id:
        :return:
        """
        qs: QuerySet = SeasonModel.objects(id=season_id)
        # retrieve unique result
        # https://mongoengine-odm.readthedocs.io/guide/querying.html#retrieving-unique-results
        try:
            season: SeasonModel = qs.get()
            return season
        except DoesNotExist:
            return None

    def update(self, id: ObjectId, data: Union[SeasonInUpdateTime, Dict[str, Any]]) -> bool:
        try:
            data = (
                data.model_dump(exclude_none=True) if isinstance(data, SeasonInUpdateTime) else data
            )
            SeasonModel.objects(id=id).update_one(**data, upsert=False)
            return True
        except Exception:
            return False

    def count(self, conditions: Dict[str, Union[str, bool, ObjectId]] = {}) -> int:
        try:
            return SeasonModel._get_collection().count_seasons(conditions)
        except Exception:
            return 0

    def list(
        self,
        page_index: int | None = None,
        page_size: int | None = None,
        match_pipeline: Optional[List[Dict[str, Any]]] = None,
        sort: Optional[Dict[str, int]] = None,
    ) -> List[SeasonModel]:
        pipeline = []
        if match_pipeline is not None:
            pipeline.append(match_pipeline)

        pipeline.append(
            {"$sort": sort if sort else {"season": 1}},
        )
        if page_index is not None and page_size is not None:
            pipeline.append({"$skip": page_size * (page_index - 1)}, {"$limit": page_size})
        try:
            docs = SeasonModel.objects().aggregate(pipeline)
            return [SeasonModel.from_mongo(doc) for doc in docs] if docs else []
        except Exception:
            return []

    def count_list(
        self,
        match_pipeline: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        pipeline = []

        if match_pipeline is not None:
            pipeline.append(match_pipeline)
        pipeline.append({"$count": "season_count"})

        try:
            docs = SeasonModel.objects().aggregate(pipeline)
            return list(docs)[0]["season_count"]
        except Exception:
            return 0

    def delete(self, id: ObjectId) -> bool:
        try:
            SeasonModel.objects(id=id).delete()
            return True
        except Exception:
            return False

    def get_current_season(self) -> Optional[SeasonModel]:
        try:
            doc = SeasonModel._get_collection().find_one({"is_current": True})
            if not doc:
                raise HTTPException(status_code=400, detail="Admin cần khởi tạo mùa")
            return SeasonModel.from_mongo(doc)
        except Exception:
            raise HTTPException(status_code=400, detail="Admin cần khởi tạo mùa")

    def bulk_update(
        self, data: Union[SeasonInUpdate, Dict[str, Any]], entities: List[SeasonModel]
    ) -> bool:
        try:
            if len(entities) == 0:
                return False

            data = (
                data.model_dump(exclude_none=True, exclude_unset=True)
                if isinstance(data, SeasonInUpdate)
                else data
            )
            operations = [
                pymongo.UpdateOne(
                    {"_id": season.id},
                    {"$set": data},
                    upsert=False,
                )
                for season in entities
            ]
            SeasonModel._get_collection().bulk_write(operations)
            return True
        except Exception:
            return False

    def find_one(self, conditions: Dict[str, Union[str, bool, ObjectId]]) -> Optional[SeasonModel]:
        try:
            doc = SeasonModel._get_collection().find_one(conditions)
            return SeasonModel.from_mongo(doc) if doc else None
        except Exception:
            return None
