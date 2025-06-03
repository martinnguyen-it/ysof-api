from typing import List, Optional
from app.domain.subject.enum import StatusSubjectEnum
from app.models.subject import SubjectModel
from app.models.subject_registration import SubjectRegistrationModel
from app.models.student import StudentModel
from app.models.subject_evaluation import SubjectEvaluationModel
from app.models.absent import AbsentModel
from app.domain.roll_call.entity import (
    StudentRollCallResultInResponse,
    SubjectRollCallResult,
    StudentRollCallResult,
)


class RollCallRepository:
    def __init__(self):
        pass

    def update_bulk(self, numerical_orders: set[int], subject: SubjectModel, current_season: int):
        """
        Updates attend_zoom in SubjectRegistrationModel based on numerical_orders
        for a given subject and season.

        Args:
            numerical_orders (list[int]): List of student numerical orders who attended zoom.
            subject (SubjectModel): Subject to update registrations for.
            current_season (int): The current season to filter students.
        """
        # Find students registered for the subject and in the current season
        registrations: List[SubjectRegistrationModel] = SubjectRegistrationModel.objects(
            subject=subject.id,
            student__in=StudentModel.objects(seasons_info__elemMatch={"season": current_season}),
        )

        # Update attend_zoom for each registration
        for registration in registrations:
            registration.update(attend_zoom=False)

            student: StudentModel = registration.student
            # Find the season info for the current season
            season_info = next(
                (info for info in student.seasons_info if info.season == current_season), None
            )

            if season_info:
                # Set attend_zoom to True if student's numerical_order
                # is in numerical_orders, else False
                attend_zoom = season_info.numerical_order in numerical_orders
                registration.update(attend_zoom=attend_zoom)

        subject.status = StatusSubjectEnum.COMPLETED
        subject.save()

        # Note: If a numerical_order in numerical_orders doesn't exist in registrations,
        # it is automatically skipped as we only process existing registrations

    def get_roll_call_results(
        self,
        season: int,
        page_index: int = 1,
        page_size: int | None = None,
        match_pipeline: Optional[dict] = None,
        sort: Optional[dict[str, int]] = None,
    ) -> StudentRollCallResultInResponse:
        """
        Get roll call results for completed subjects.
        """
        # Get completed subjects
        completed_subjects = SubjectModel.objects(status=StatusSubjectEnum.COMPLETED, season=season)
        if not completed_subjects:
            return []

        # Get students based on match pipeline
        pipeline = []
        if match_pipeline is not None:
            pipeline.append({"$match": match_pipeline})
        pipeline.append(
            {"$sort": sort if sort else {"seasons_info.numerical_order": 1}},
        )
        if isinstance(page_size, int):
            pipeline.extend(
                [
                    {"$skip": page_size * (page_index - 1)},
                    {"$limit": page_size},
                ]
            )

        students = StudentModel.objects().aggregate(pipeline)
        if not students:
            return []

        # Process each student
        results = []
        total = 0

        summary = {}
        for subject in completed_subjects:
            summary[str(subject.id)] = {
                "absent": 0,
                "completed": 0,
                "no_complete": 0,
            }

        for student in students:
            student_model = StudentModel.from_mongo(student)
            total += 1
            subject_completed = 0
            subject_not_completed = 0
            # Get student's subject registrations
            subject_results = {}
            for subject in completed_subjects:
                # Check registration
                registration = SubjectRegistrationModel.objects(
                    student=student_model.id, subject=subject.id
                ).first()

                if not registration:
                    # subject_results[str(subject.id)] = None
                    continue

                # Check evaluation
                evaluation = SubjectEvaluationModel.objects(
                    student=student_model.id, subject=subject.id
                ).first()

                # Check absent
                absent = AbsentModel.objects(
                    student=student_model.id, subject=subject.id, status=True
                ).first()

                # Ensure attend_zoom is a boolean
                attend_zoom = False
                if registration and hasattr(registration, "attend_zoom"):
                    attend_zoom = bool(registration.attend_zoom)

                subject_results[str(subject.id)] = SubjectRollCallResult(
                    attend_zoom=attend_zoom,
                    evaluation=bool(evaluation),
                    absent_type=absent.type if absent else None,
                    result=None,  # Will be computed by the property
                )
                if subject_results[str(subject.id)].result == "completed":
                    subject_completed += 1
                    summary[str(subject.id)]["completed"] += 1
                elif subject_results[str(subject.id)].result == "no_complete":
                    subject_not_completed += 1
                    summary[str(subject.id)]["no_complete"] += 1
                else:
                    summary[str(subject.id)]["absent"] += 1

            results.append(
                StudentRollCallResult(
                    id=str(student_model.id),
                    numerical_order=next(
                        (info.numerical_order for info in student_model.seasons_info), 0
                    ),
                    holy_name=student_model.holy_name,
                    full_name=student_model.full_name,
                    subjects=subject_results,
                    subject_completed=subject_completed,
                    subject_not_completed=subject_not_completed,
                )
            )

        return StudentRollCallResultInResponse(
            data=results,
            summary=summary,
        )
