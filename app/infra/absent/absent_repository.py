"""Absent repository module"""

from typing import Optional, Dict, Union, List, Any
from bson import ObjectId
from app.domain.absent.entity import AbsentInDB, AbsentInUpdateTime
from app.models.absent import AbsentModel


class AbsentRepository:
    def __init__(self):
        pass

    def create(self, doc: AbsentInDB) -> AbsentModel:
        """
        Create new doc in db
        :param doc:
        :return:
        """
        # create doc instance
        new_doc = AbsentModel(**doc.model_dump())
        # and save it to db
        new_doc.save()

        return new_doc

    def find_one(self, conditions: list[str, str | bool | ObjectId]) -> AbsentModel | None:
        try:
            doc = AbsentModel._get_collection().find_one(conditions)
            return AbsentModel.from_mongo(doc) if doc else None
        except Exception:
            return None

    def update(self, id: ObjectId, data: Union[AbsentInUpdateTime, Dict[str, Any]]) -> bool:
        try:
            data = data.model_dump(exclude_none=True) if isinstance(data, AbsentInUpdateTime) else data
            AbsentModel.objects(id=id).update_one(**data, upsert=False)
            return True
        except Exception:
            return False

    def count(self, conditions: Dict[str, Union[str, bool, ObjectId]] = {}) -> int:
        try:
            return AbsentModel._get_collection().count_docs(conditions)
        except Exception:
            return 0

    def list(
        self,
        match_pipeline: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, int]] = None,
    ) -> List[AbsentModel]:
        pipeline = [
            {"$sort": sort if sort else {"id": 1}},
        ]

        if match_pipeline is not None:
            pipeline.append({"$match": match_pipeline})

        try:
            docs = AbsentModel.objects().aggregate(pipeline)
            return [AbsentModel.from_mongo(doc) for doc in docs] if docs else []
        except Exception:
            return []

    def delete(self, id: ObjectId) -> bool:
        try:
            AbsentModel.objects(id=id).delete()
            return True
        except Exception:
            return False
