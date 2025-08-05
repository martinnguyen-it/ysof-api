"""Student repository module"""

from typing import Optional, Dict, Union, List, Any
from mongoengine import QuerySet, DoesNotExist
from bson import ObjectId

from app.models.student import StudentModel
from app.domain.student.entity import StudentInDB, StudentInUpdate
from app.domain.subject.entity import (
    _SubjectRegistrationInResponse,
    ListSubjectRegistrationInResponse,
    StudentInSubject,
)
from app.domain.shared.entity import Pagination


class StudentRepository:
    def __init__(self):
        pass

    def create(self, student: StudentInDB) -> StudentInDB:
        """
        Create new student in db
        :param student:
        :return:
        """
        # create student document instance
        new_student = StudentModel(**student.model_dump())
        # and save it to db
        new_student.save()

        return StudentInDB.model_validate(new_student)

    def get_by_id(self, student_id: Union[str, ObjectId]) -> Optional[StudentModel]:
        """
        Get student in db from id
        :param student_id:
        :return:
        """
        qs: QuerySet = StudentModel.objects(id=student_id)
        # retrieve unique result
        # https://mongoengine-odm.readthedocs.io/guide/querying.html#retrieving-unique-results
        try:
            student: StudentModel = qs.get()
            return student
        except DoesNotExist:
            return None

    def get_by_email(self, email: str) -> Optional[StudentModel]:
        """
        Get student in db from email
        :param student_email:
        :return:
        """
        qs: QuerySet = StudentModel.objects(email=email)
        # retrieve unique result
        # https://mongoengine-odm.readthedocs.io/guide/querying.html#retrieving-unique-results
        try:
            student = qs.get()
        except DoesNotExist:
            return None
        return student

    def update(self, id: ObjectId, data: Union[StudentInUpdate, Dict[str, Any]]) -> bool:
        try:
            data = data.model_dump(exclude_none=True) if isinstance(data, StudentInUpdate) else data
            StudentModel.objects(id=id).update_one(**data, upsert=False)
            return True
        except Exception:
            return False

    def count(self, conditions: Dict[str, Union[str, bool, ObjectId]] = {}) -> int:
        try:
            return StudentModel._get_collection().count_documents(conditions)
        except Exception:
            return 0

    def list(
        self,
        page_index: int = 1,
        page_size: int | None = None,
        match_pipeline: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, int]] = None,
    ) -> List[StudentModel]:
        pipeline = []
        if match_pipeline is not None:
            pipeline.append({"$match": match_pipeline})
        pipeline.append(
            {"$sort": sort if sort else {"created_at": -1}},
        )
        if isinstance(page_size, int):
            pipeline.extend(
                [
                    {"$skip": page_size * (page_index - 1)},
                    {"$limit": page_size},
                ]
            )

        try:
            docs = StudentModel.objects().aggregate(pipeline)
            return [StudentModel.from_mongo(doc) for doc in docs] if docs else []
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
            docs = StudentModel.objects().aggregate(pipeline)
            return list(docs)[0]["document_count"]
        except Exception:
            return 0

    def delete(self, id: ObjectId) -> bool:
        try:
            StudentModel.objects(id=id).delete()
            return True
        except Exception:
            return False

    def find_one(self, conditions: Dict[str, Union[str, bool, ObjectId]]) -> Optional[StudentModel]:
        try:
            doc = StudentModel._get_collection().find_one(conditions)
            return StudentModel.from_mongo(doc) if doc else None
        except Exception:
            return None

    def list_subject_registrations(
        self,
        page_index: int = 1,
        page_size: int | None = None,
        match_pipeline: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, int]] = None,
    ):
        total = self.count_list(match_pipeline=match_pipeline)
        resp = ListSubjectRegistrationInResponse(
            data=[], pagination=Pagination(total_pages=0, total=total)
        )
        total_pages = 0

        # Optimized: Single aggregation pipeline using $facet for both summary and data
        pipeline = []
        if match_pipeline:
            pipeline.append({"$match": match_pipeline})

        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "SubjectRegistration",
                        "localField": "_id",
                        "foreignField": "student",
                        "as": "subject_registrations",
                    }
                },
                {
                    "$facet": {
                        "summary": [
                            {"$unwind": "$subject_registrations"},
                            {
                                "$group": {
                                    "_id": "$subject_registrations.subject",
                                    "count": {"$sum": 1},
                                }
                            },
                        ],
                        "data": [
                            {"$sort": sort if sort else {"seasons_info.numerical_order": 1}},
                            {"$skip": page_size * (page_index - 1)},
                            {"$limit": page_size},
                        ],
                    }
                },
            ]
        )

        cursor = StudentModel.objects().aggregate(pipeline)
        result = list(cursor)[0] if cursor.alive else {"summary": [], "data": []}

        # Process summary
        summary = {}
        for record in result.get("summary", []):
            summary[str(record["_id"])] = record["count"]
        resp.summary = summary

        # Process data
        for record in result.get("data", []):
            total_pages = total_pages + 1
            total_regis = len(record.get("subject_registrations"))
            subject_registrations = (
                [str(doc["subject"]) for doc in record.get("subject_registrations")]
                if total_regis > 0
                else []
            )
            record.pop("subject_registrations")
            student = StudentInSubject(
                **StudentInDB.model_validate(StudentModel.from_mongo(record)).model_dump()
            )
            resp.data.append(
                _SubjectRegistrationInResponse(
                    student=student, subject_registrations=subject_registrations, total=total_regis
                )
            )
        resp.pagination = Pagination(total=total, total_pages=total_pages, page_index=page_index)
        return resp
