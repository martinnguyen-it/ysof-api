"""Subject repository module"""

from bson import ObjectId
from app.models.subject_registration import SubjectRegistrationModel
from app.domain.subject.entity import SubjectRegistrationInResponse


class SubjectRegistrationRepository:
    def __init__(self):
        pass

    def insert_many(self, student_id: ObjectId, subject_ids: list[ObjectId | str]):
        try:
            if len(subject_ids) == 0:
                return False

            instances = [
                SubjectRegistrationModel(**{"student": student_id, "subject": ObjectId(subject_id)})
                for subject_id in subject_ids
            ]

            SubjectRegistrationModel.objects.insert(instances, load_bulk=False)

            return True
        except Exception:
            return False

    def delete_by_student_id(self, id: ObjectId) -> bool:
        try:
            SubjectRegistrationModel._get_collection().delete_many({"student": id})
            return True
        except Exception:
            return False

    def get_by_student_id(self, student_id: ObjectId) -> SubjectRegistrationInResponse | None:
        pipeline = [
            {"$match": {"student": student_id}},  # Filter by student ID
            {"$group": {"_id": "$student", "subjects_registration": {"$push": "$subject"}}},
            {"$project": {"student_id": "$_id", "subjects_registration": 1, "_id": 0}},
        ]

        try:
            cursor = SubjectRegistrationModel.objects().aggregate(pipeline)
            return SubjectRegistrationInResponse(**list(cursor)[0]) if cursor.alive else None
        except Exception:
            return None

    def find_one(self, conditions: list[str, str | bool | ObjectId]) -> SubjectRegistrationModel | None:
        try:
            doc = SubjectRegistrationModel._get_collection().find_one(conditions)
            return SubjectRegistrationModel.from_mongo(doc) if doc else None
        except Exception:
            return None
