"""Lecturer repository module"""
from typing import Optional, Dict, Union, List, Any
from mongoengine import QuerySet, DoesNotExist
from bson import ObjectId

from app.models.lecturer import LecturerModel
from app.domain.lecturer.entity import LecturerInDB, LecturerInUpdateTime


class LecturerRepository:
    def __init__(self):
        pass

    def create(self, lecturer: LecturerInDB) -> LecturerModel:
        """
        Create new lecturer in db
        :param lecturer:
        :return:
        """
        # create lecturer instance
        new_doc = LecturerModel(**lecturer.model_dump())
        # and save it to db
        new_doc.save()

        return new_doc

    def get_by_id(self, lecturer_id: Union[str, ObjectId]) -> Optional[LecturerModel]:
        """
        Get lecturer in db from id
        :param lecturer_id:
        :return:
        """
        qs: QuerySet = LecturerModel.objects(id=lecturer_id)
        # retrieve unique result
        # https://mongoengine-odm.readthedocs.io/guide/querying.html#retrieving-unique-results
        try:
            lecturer: LecturerModel = qs.get()
            return lecturer
        except DoesNotExist:
            return None

    def update(self, id: ObjectId, data: Union[LecturerInUpdateTime, Dict[str, Any]]) -> bool:
        try:
            data = data.model_dump(exclude_none=True) if isinstance(
                data, LecturerInUpdateTime) else data
            LecturerModel.objects(id=id).update_one(**data, upsert=False)
            return True
        except Exception:
            return False

    def count(self, conditions: Dict[str, Union[str, bool, ObjectId]] = {}) -> int:
        try:
            return LecturerModel._get_collection().count_lecturers(conditions)
        except Exception:
            return 0

    def list(self,
             page_index: int = 1,
             page_size: int = 20,
             match_pipeline: Optional[Dict[str, Any]] = None,
             sort: Optional[Dict[str, int]] = None,
             ) -> List[LecturerModel]:
        pipeline = [
            {"$sort": sort if sort else {"created_at": -1}},
            {"$skip": page_size * (page_index - 1)},
            {"$limit": page_size}
        ]

        if match_pipeline is not None:
            pipeline.append(match_pipeline)

        try:
            docs = LecturerModel.objects().aggregate(pipeline)
            return [LecturerModel.from_mongo(doc) for doc in docs] if docs else []
        except Exception:
            return []

    def count_list(self,
                   match_pipeline: Optional[Dict[str, Any]] = None,
                   ) -> int:
        pipeline = []

        if match_pipeline is not None:
            pipeline.append(match_pipeline)
        pipeline.append({"$count": "lecturer_count"})

        try:
            docs = LecturerModel.objects().aggregate(pipeline)
            return list(docs)[0]['lecturer_count']
        except Exception:
            return 0

    def delete(self, id: ObjectId) -> bool:
        try:
            LecturerModel.objects(id=id).delete()
            return True
        except Exception:
            return False

    def find_one(self, conditions: Dict[str, Union[str, bool, ObjectId]]) -> Optional[LecturerModel]:
        try:
            doc = LecturerModel._get_collection().find_one(conditions)
            return LecturerModel.from_mongo(doc) if doc else None
        except Exception:
            return None
