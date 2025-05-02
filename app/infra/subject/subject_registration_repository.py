"""Subject repository module"""

from bson import ObjectId
from app.models.student import StudentModel
from app.models.subject_registration import SubjectRegistrationModel
from app.domain.subject.entity import SubjectRegistrationInResponse
from app.shared.utils.general import get_current_season_value


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

    def get_by_subject_id(
        self, subject_id: ObjectId, search: str | None = None
    ) -> list[StudentModel]:
        """
        Retrieves a list of SubjectRegistrationModel instances for a given subject_id,
        with optional search by holy_name, full_name, or numerical_order in the current season.

        Args:
            subject_id (ObjectId): The ID of the subject to query registrations for.
            search (str | None): Optional search string to filter by holy_name, full_name,
                                or numerical_order.

        Returns:
            List[StudentModel]: List of matching subject registrations.
        """
        pipeline = [
            {"$match": {"subject": subject_id}},
            {
                "$lookup": {
                    "from": "Students",
                    "localField": "student",
                    "foreignField": "_id",
                    "as": "student_info",
                }
            },
            {"$unwind": "$student_info"},
        ]

        current_season = get_current_season_value()
        if search:
            try:
                num = int(search)
                search_conditions = [
                    {"student_info.holy_name": {"$regex": search, "$options": "i"}},
                    {"student_info.full_name": {"$regex": search, "$options": "i"}},
                    {
                        "student_info.seasons_info": {
                            "$elemMatch": {"season": current_season, "numerical_order": num}
                        }
                    },
                ]
            except ValueError:
                # If search is not a number, only search by holy_name and full_name
                search_conditions = [
                    {"student_info.holy_name": {"$regex": search, "$options": "i"}},
                    {"student_info.full_name": {"$regex": search, "$options": "i"}},
                ]

            pipeline.append({"$match": {"$or": search_conditions}})

        # Add sorting by numerical_order for the current season
        pipeline.extend(
            [
                {
                    "$addFields": {
                        "numerical_order": {
                            "$arrayElemAt": [
                                {
                                    "$filter": {
                                        "input": "$student_info.seasons_info",
                                        "as": "season",
                                        "cond": {"$eq": ["$$season.season", current_season]},
                                    }
                                },
                                0,
                            ]
                        }
                    }
                },
                {"$sort": {"numerical_order.numerical_order": 1}},
            ]
        )
        try:
            cursor = SubjectRegistrationModel.objects().aggregate(pipeline)
            results = [StudentModel.from_mongo(doc["student_info"]) for doc in cursor]
            return results
        except Exception:
            return []

    def find_one(
        self, conditions: list[str, str | bool | ObjectId]
    ) -> SubjectRegistrationModel | None:
        try:
            doc = SubjectRegistrationModel._get_collection().find_one(conditions)
            return SubjectRegistrationModel.from_mongo(doc) if doc else None
        except Exception:
            return None
