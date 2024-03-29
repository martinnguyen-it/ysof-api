"""Admin repository module"""
from typing import Optional, Dict, Union, List, Any
from mongoengine import QuerySet, DoesNotExist
from bson import ObjectId

from app.models.admin import AdminModel
from app.domain.admin.entity import AdminInDB, AdminInUpdate


class AdminRepository:
    def __init__(self):
        pass

    def create(self, admin: AdminInDB) -> AdminInDB:
        """
        Create new admin in db
        :param admin:
        :return:
        """
        # create admin document instance
        new_admin = AdminModel(**admin.model_dump())
        # and save it to db
        new_admin.save()

        return AdminInDB.model_validate(new_admin)

    def get_by_id(self, admin_id: Union[str, ObjectId]) -> Optional[AdminModel]:
        """
        Get admin in db from id
        :param admin_id:
        :return:
        """
        qs: QuerySet = AdminModel.objects(id=admin_id)
        # retrieve unique result
        # https://mongoengine-odm.readthedocs.io/guide/querying.html#retrieving-unique-results
        try:
            admin: AdminModel = qs.get()
            return admin
        except DoesNotExist:
            return None

    def get_by_email(self, email: str) -> Optional[AdminModel]:
        """
        Get admin in db from email
        :param admin_email:
        :return:
        """
        qs: QuerySet = AdminModel.objects(email=email)
        # retrieve unique result
        # https://mongoengine-odm.readthedocs.io/guide/querying.html#retrieving-unique-results
        try:
            admin = qs.get()
        except DoesNotExist:
            return None
        return admin

    def update(self, id: ObjectId, data: Union[AdminInUpdate, Dict[str, Any]]) -> bool:
        try:
            data = data.model_dump(exclude_none=True) if isinstance(
                data, AdminInUpdate) else data
            AdminModel.objects(id=id).update_one(**data, upsert=False)
            return True
        except Exception:
            return False

    def count(self, conditions: Dict[str, Union[str, bool, ObjectId]] = {}) -> int:
        try:
            return AdminModel._get_collection().count_documents(conditions)
        except Exception:
            return 0

    def list(self,
             page_index: int = 1,
             page_size: int = 20,
             match_pipeline: Optional[Dict[str, Any]] = None,
             sort: Optional[Dict[str, int]] = None,
             ) -> List[AdminModel]:
        pipeline = [
            {"$sort": sort if sort else {"created_at": -1}},
            {"$skip": page_size * (page_index - 1)},
            {"$limit": page_size}
        ]

        if match_pipeline is not None:
            pipeline.append({
                "$match": match_pipeline
            })
        print(pipeline)
        try:
            docs = AdminModel.objects().aggregate(pipeline)
            return [AdminModel.from_mongo(doc) for doc in docs] if docs else []
        except Exception:
            return []

    def count_list(self,
                   match_pipeline: Optional[Dict[str, Any]] = None,
                   ) -> int:
        pipeline = []

        if match_pipeline is not None:
            pipeline.append({
                "$match": match_pipeline
            })
        pipeline.append({"$count": "document_count"})

        try:
            docs = AdminModel.objects().aggregate(pipeline)
            return list(docs)[0]['document_count']
        except Exception:
            return 0
