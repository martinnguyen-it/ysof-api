"""SubjectEvaluation repository module"""

from typing import Optional, Dict, Union, List, Any
from bson import ObjectId

from app.models.subject_evaluation import SubjectEvaluationModel
from app.domain.subject.subject_evaluation.entity import (
    SubjectEvaluationInDB,
    SubjectEvaluationInUpdateTime,
)


class SubjectEvaluationRepository:
    def __init__(self):
        pass

    def create(self, doc: SubjectEvaluationInDB) -> SubjectEvaluationModel:
        """
        Create new doc in db
        :param doc:
        :return:
        """
        # create doc instance
        new_doc = SubjectEvaluationModel(**doc.model_dump())
        # and save it to db
        new_doc.save()

        return new_doc

    def find_one(self, conditions: list[str, str | bool | ObjectId]) -> SubjectEvaluationModel | None:
        try:
            doc = SubjectEvaluationModel._get_collection().find_one(conditions)
            return SubjectEvaluationModel.from_mongo(doc) if doc else None
        except Exception:
            return None

    def update(self, id: ObjectId, data: Union[SubjectEvaluationInUpdateTime, Dict[str, Any]]) -> bool:
        try:
            data = data.model_dump(exclude_none=True) if isinstance(data, SubjectEvaluationInUpdateTime) else data
            SubjectEvaluationModel.objects(id=id).update_one(**data, upsert=False)
            return True
        except Exception:
            return False

    def count(self, conditions: Dict[str, Union[str, bool, ObjectId]] = {}) -> int:
        try:
            return SubjectEvaluationModel._get_collection().count_docs(conditions)
        except Exception:
            return 0

    def list(
        self,
        match_pipeline: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, int]] = None,
    ) -> List[SubjectEvaluationModel]:
        pipeline = [
            {"$sort": sort if sort else {"subject": 1}},
        ]

        if match_pipeline is not None:
            pipeline.append({"$match": match_pipeline})

        try:
            docs = SubjectEvaluationModel.objects().aggregate(pipeline)
            return [SubjectEvaluationModel.from_mongo(doc) for doc in docs] if docs else []
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
            docs = SubjectEvaluationModel.objects().aggregate(pipeline)
            return list(docs)[0]["doc_count"]
        except Exception:
            return 0

    def delete(self, id: ObjectId) -> bool:
        try:
            SubjectEvaluationModel.objects(id=id).delete()
            return True
        except Exception:
            return False
