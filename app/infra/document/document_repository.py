"""Document repository module"""
from typing import Optional, Dict, Union, List, Any
from mongoengine import QuerySet, DoesNotExist
from bson import ObjectId

from app.models.document import DocumentModel
from app.domain.document.entity import DocumentInDB, DocumentInUpdateTime


class DocumentRepository:
    def __init__(self):
        pass

    def create(self, document: DocumentInDB) -> DocumentModel:
        """
        Create new document in db
        :param document:
        :return:
        """
        # create document instance
        new_doc = DocumentModel(**document.model_dump())
        # and save it to db
        new_doc.save()

        return new_doc

    def get_by_id(self, document_id: Union[str, ObjectId]) -> Optional[DocumentModel]:
        """
        Get document in db from id
        :param document_id:
        :return:
        """
        qs: QuerySet = DocumentModel.objects(id=document_id)
        # retrieve unique result
        # https://mongoengine-odm.readthedocs.io/guide/querying.html#retrieving-unique-results
        try:
            document: DocumentModel = qs.get()
            return document
        except DoesNotExist:
            return None

    def update(self, id: ObjectId, data: Union[DocumentInUpdateTime, Dict[str, Any]]) -> bool:
        try:
            data = data.model_dump(exclude_none=True) if isinstance(
                data, DocumentInUpdateTime) else data
            DocumentModel.objects(id=id).update_one(**data, upsert=False)
            return True
        except Exception:
            return False

    def count(self, conditions: Dict[str, Union[str, bool, ObjectId]] = {}) -> int:
        try:
            return DocumentModel._get_collection().count_documents(conditions)
        except Exception:
            return 0

    def list(self,
             page_index: int = 1,
             page_size: int = 20,
             match_pipeline: Optional[List[Dict[str, Any]]] = None,
             sort: Optional[Dict[str, int]] = None,
             ) -> List[DocumentModel]:
        pipeline = [
            {"$sort": sort if sort else {"created_at": -1}},
            {"$skip": page_size * (page_index - 1)},
            {"$limit": page_size}
        ]

        if match_pipeline is not None:
            pipeline.extend(match_pipeline)

        try:
            docs = DocumentModel.objects().aggregate(pipeline)
            return [DocumentModel.from_mongo(doc) for doc in docs] if docs else []
        except Exception:
            return []

    def count_list(self,
                   match_pipeline: Optional[List[Dict[str, Any]]] = None,
                   ) -> int:
        pipeline = []

        if match_pipeline is not None:
            pipeline.extend(match_pipeline)
        pipeline.append({"$count": "document_count"})

        try:
            docs = DocumentModel.objects().aggregate(pipeline)
            return list(docs)[0]['document_count']
        except Exception:
            return 0

    def delete(self, id: ObjectId) -> bool:
        try:
            DocumentModel.objects(id=id).delete()
            return True
        except Exception:
            return False
