"""GeneralTask repository module"""
from typing import Optional, Dict, Union, List, Any
from mongoengine import QuerySet, DoesNotExist
from bson import ObjectId

from app.models.general_task import GeneralTaskModel
from app.domain.general_task.entity import GeneralTaskInDB, GeneralTaskInUpdateTime


class GeneralTaskRepository:
    def __init__(self):
        pass

    def create(self, general_task: GeneralTaskInDB, attachments: Optional[List[str]] = []) -> GeneralTaskModel:
        """
        Create new general_task in db
        :param general_task:
        :return:
        """
        # create general_task instance
        new_doc = GeneralTaskModel(**general_task.model_dump())
        new_doc.attachments = [ObjectId(id) for id in attachments]
        # and save it to db
        new_doc.save()

        return new_doc

    def get_by_id(self, general_task_id: Union[str, ObjectId]) -> Optional[GeneralTaskModel]:
        """
        Get general_task in db from id
        :param general_task_id:
        :return:
        """
        qs: QuerySet = GeneralTaskModel.objects(id=general_task_id)
        # retrieve unique result
        # https://mongoengine-odm.readthedocs.io/guide/querying.html#retrieving-unique-results
        try:
            general_task: GeneralTaskModel = qs.get()
            return general_task
        except DoesNotExist:
            return None

    def update(self, id: ObjectId, data: Union[GeneralTaskInUpdateTime, Dict[str, Any]]) -> bool:
        try:
            attachments = data.attachments
            data = data.model_dump(exclude_none=True, exclude={"attachments"}) if isinstance(
                data, GeneralTaskInUpdateTime) else data
            if isinstance(attachments, List):
                data["attachments"] = [ObjectId(id) for id in attachments]
            print(data)
            GeneralTaskModel.objects(id=id).update_one(**data, upsert=False)
            return True
        except Exception as e:
            print(e)
            return False

    def count(self, conditions: Dict[str, Union[str, bool, ObjectId]] = {}) -> int:
        try:
            return GeneralTaskModel._get_collection().count_general_tasks(conditions)
        except Exception:
            return 0

    def list(self,
             page_index: int = 1,
             page_size: int = 20,
             match_pipeline: Optional[List[Dict[str, Any]]] = None,
             sort: Optional[Dict[str, int]] = None,
             ) -> List[GeneralTaskModel]:
        pipeline = [
            {"$sort": sort if sort else {"created_at": -1}},
            {"$skip": page_size * (page_index - 1)},
            {"$limit": page_size}
        ]

        if match_pipeline is not None:
            pipeline.extend(match_pipeline)

        try:
            docs = GeneralTaskModel.objects().aggregate(pipeline)
            return [GeneralTaskModel.from_mongo(doc) for doc in docs] if docs else []
        except Exception:
            return []

    def count_list(self,
                   match_pipeline: Optional[List[Dict[str, Any]]] = None,
                   ) -> int:
        pipeline = []

        if match_pipeline is not None:
            pipeline.extend(match_pipeline)
        pipeline.append({"$count": "general_task_count"})

        try:
            docs = GeneralTaskModel.objects().aggregate(pipeline)
            return list(docs)[0]['general_task_count']
        except Exception:
            return 0

    def delete(self, id: ObjectId) -> bool:
        try:
            GeneralTaskModel.objects(id=id).delete()
            return True
        except Exception:
            return False
