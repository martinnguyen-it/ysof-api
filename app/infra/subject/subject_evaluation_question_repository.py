"""SubjectEvaluationQuestion repository module"""

from typing import Optional, Dict, Union, List, Any
from mongoengine import QuerySet, DoesNotExist
from bson import ObjectId

from app.models.subject_evaluation import SubjectEvaluationQuestionModel
from app.domain.subject.subject_evaluation.entity import (
    SubjectEvaluationQuestionInDB,
    SubjectEvaluationQuestionInUpdateTime,
)


class SubjectEvaluationQuestionRepository:
    def __init__(self):
        pass

    def create(self, doc: SubjectEvaluationQuestionInDB) -> SubjectEvaluationQuestionModel:
        """
        Create new doc in db
        :param doc:
        :return:
        """
        # create doc instance
        new_doc = SubjectEvaluationQuestionModel(**doc.model_dump())
        # and save it to db
        new_doc.save()

        return new_doc

    def get_by_subject_id(self, subject_id: Union[str, ObjectId]) -> Optional[SubjectEvaluationQuestionModel]:
        """
        Get doc in db from subject_id
        :param subject_id:
        :return:
        """
        qs: QuerySet = SubjectEvaluationQuestionModel.objects(subject=subject_id)
        # retrieve unique result
        # https://mongoengine-odm.readthedocs.io/guide/querying.html#retrieving-unique-results
        try:
            doc: SubjectEvaluationQuestionModel = qs.get()
            return doc
        except DoesNotExist:
            return None

    def update(self, id: ObjectId, data: Union[SubjectEvaluationQuestionInUpdateTime, Dict[str, Any]]) -> bool:
        try:
            data = (
                data.model_dump(exclude_none=True) if isinstance(data, SubjectEvaluationQuestionInUpdateTime) else data
            )
            SubjectEvaluationQuestionModel.objects(id=id).update_one(**data, upsert=False)
            return True
        except Exception:
            return False

    def count(self, conditions: Dict[str, Union[str, bool, ObjectId]] = {}) -> int:
        try:
            return SubjectEvaluationQuestionModel._get_collection().count_docs(conditions)
        except Exception:
            return 0

    def list(
        self,
        match_pipeline: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, int]] = None,
    ) -> List[SubjectEvaluationQuestionModel]:
        pipeline = []
        if match_pipeline is not None:
            pipeline.append({"$match": match_pipeline})

        pipeline.append(
            {"$sort": sort if sort else {"created_at": -1}},
        )

        try:
            docs = SubjectEvaluationQuestionModel.objects().aggregate(pipeline)
            return [SubjectEvaluationQuestionModel.from_mongo(doc) for doc in docs] if docs else []
        except Exception:
            return []

    def count_list(
        self,
        match_pipeline: Optional[Dict[str, Any]] = None,
    ) -> int:
        pipeline = []

        if match_pipeline is not None:
            pipeline.append({"$match": match_pipeline})
        pipeline.append({"$count": "doc_count"})

        try:
            docs = SubjectEvaluationQuestionModel.objects().aggregate(pipeline)
            return list(docs)[0]["doc_count"]
        except Exception:
            return 0

    def delete(self, id: ObjectId) -> bool:
        try:
            SubjectEvaluationQuestionModel.objects(id=id).delete()
            return True
        except Exception:
            return False
