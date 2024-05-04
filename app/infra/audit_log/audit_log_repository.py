"""Log repository module"""

from typing import Optional, Dict, Union, List, Any
from mongoengine import QuerySet, DoesNotExist
from bson import ObjectId

from app.models.audit_log import AuditLogModel
from app.domain.audit_log.entity import AuditLogInDB


class AuditLogRepository:
    def __init__(self):
        pass

    def create(self, audit_log: AuditLogInDB) -> AuditLogModel:
        """
        Create new audit_log in db
        :param audit_log:
        :return:
        """
        # create audit_log instance
        new_doc = AuditLogModel(**audit_log.model_dump())
        # and save it to db
        new_doc.save()

        return new_doc

    def get_by_id(self, document_id: Union[str, ObjectId]) -> Optional[AuditLogModel]:
        """
        Get audit_log in db from id
        :param document_id:
        :return:
        """
        qs: QuerySet = AuditLogModel.objects(id=document_id)
        # retrieve unique result
        # https://mongoengine-odm.readthedocs.io/guide/querying.html#retrieving-unique-results
        try:
            audit_log: AuditLogModel = qs.get()
            return audit_log
        except DoesNotExist:
            return None

    def count(self, conditions: Dict[str, Union[str, bool, ObjectId]] = {}) -> int:
        try:
            return AuditLogModel._get_collection().count_documents(conditions)
        except Exception:
            return 0

    def list(
        self,
        page_index: int = 1,
        page_size: int = 20,
        match_pipeline: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, int]] = None,
    ) -> List[AuditLogModel]:
        pipeline = []

        if match_pipeline is not None:
            pipeline.append({"$match": match_pipeline})

        pipeline.extend(
            [
                {"$sort": sort if sort else {"created_at": -1}},
                {"$skip": page_size * (page_index - 1)},
                {"$limit": page_size},
            ]
        )

        try:
            docs = AuditLogModel.objects().aggregate(pipeline)
            return [AuditLogModel.from_mongo(doc) for doc in docs] if docs else []
        except Exception:
            return []

    def count_list(
        self,
        match_pipeline: Optional[Dict[str, Any]] = None,
    ) -> int:
        pipeline = []

        if match_pipeline is not None:
            pipeline.append({"$match": match_pipeline})
        pipeline.append({"$count": "document_count"})

        try:
            docs = AuditLogModel.objects().aggregate(pipeline)
            return list(docs)[0]["document_count"]
        except Exception:
            return 0

    def delete(self, id: ObjectId) -> bool:
        try:
            AuditLogModel.objects(id=id).delete()
            return True
        except Exception:
            return False
