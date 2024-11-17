from fastapi import Depends
from app.shared import request_object, use_case, response_object
from app.domain.subject.entity import SubjectInDB
from app.domain.subject.subject_evaluation.entity import (
    LecturerInEvaluation,
    ManySubjectEvaluationAdminInResponse,
    StudentInEvaluation,
    SubjectEvaluationAdmin,
    SubjectEvaluationInDB,
    SubjectInEvaluation,
)
from app.infra.subject.subject_evaluation_repository import SubjectEvaluationRepository
from app.domain.lecturer.entity import LecturerInDB
from app.models.subject_evaluation import SubjectEvaluationModel
from app.shared.utils.general import get_current_season_value
from app.models.subject import SubjectModel
from app.infra.subject.subject_repository import SubjectRepository
from app.domain.shared.entity import Pagination
import math
from app.domain.student.entity import StudentInDB
from app.infra.student.student_repository import StudentRepository
from app.models.student import StudentModel


class ListSubjectEvaluationRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        page_index: int,
        page_size: int,
        sort: str,
        subject_id: str,
        search: str | None = None,
    ):
        self.page_index = page_index
        self.page_size = page_size
        self.sort = sort
        self.subject_id = subject_id
        self.search = search

    @classmethod
    def builder(
        cls,
        page_index: int,
        page_size: int,
        sort: str,
        subject_id: str,
        search: str | None = None,
    ) -> request_object.RequestObject:
        return ListSubjectEvaluationRequestObject(
            page_index=page_index,
            page_size=page_size,
            search=search,
            sort=sort,
            subject_id=subject_id,
        )


class ListSubjectEvaluationUseCase(use_case.UseCase):
    def __init__(
        self,
        student_repository: StudentRepository = Depends(StudentRepository),
        subject_evaluation_repository: SubjectEvaluationRepository = Depends(
            SubjectEvaluationRepository
        ),
        subject_repository: SubjectRepository = Depends(SubjectRepository),
    ):
        self.subject_evaluation_repository = subject_evaluation_repository
        self.subject_repository = subject_repository
        self.student_repository = student_repository

    def process_request(self, req_object: ListSubjectEvaluationRequestObject):
        current_season: int = get_current_season_value()
        subject: SubjectModel | None = self.subject_repository.get_by_id(req_object.subject_id)
        if subject is None or subject.season != current_season:
            return response_object.ResponseFailure.build_not_found_error(
                message="Môn học không tồn tại hoặc thuộc mùa cũ."
            )

        match_pipeline = {"subject": subject.id}

        if isinstance(req_object.search, str):
            try:
                numerical_order = int(req_object.search)
            except Exception:
                numerical_order = None
            students: list[StudentModel] = self.student_repository.list(
                match_pipeline={
                    "$or": [
                        {"full_name": {"$regex": req_object.search, "$options": "i"}},
                        {"numerical_order": numerical_order},
                    ]
                },
                page_size=100,
            )
            match_pipeline = {
                **match_pipeline,
                "student": {"$in": [student.id for student in students]},
            }

        docs: list[SubjectEvaluationModel] = self.subject_evaluation_repository.list(
            match_pipeline=match_pipeline,
            sort=req_object.sort,
            page_size=req_object.page_size,
            page_index=req_object.page_index,
        )

        total = self.subject_evaluation_repository.count_list(match_pipeline=match_pipeline)

        return ManySubjectEvaluationAdminInResponse(
            pagination=Pagination(
                total=total,
                page_index=req_object.page_index,
                total_pages=math.ceil(total / req_object.page_size),
            ),
            data=[
                SubjectEvaluationAdmin(
                    **SubjectEvaluationInDB.model_validate(subject_evaluation).model_dump(
                        exclude={"student", "subject"}
                    ),
                    subject=SubjectInEvaluation(
                        **SubjectInDB.model_validate(subject_evaluation.subject).model_dump(
                            exclude=({"lecturer"})
                        ),
                        lecturer=LecturerInEvaluation(
                            **LecturerInDB.model_validate(
                                subject_evaluation.subject.lecturer
                            ).model_dump()
                        ),
                    ),
                    student=StudentInEvaluation(
                        **StudentInDB.model_validate(subject_evaluation.student).model_dump()
                    ),
                )
                for subject_evaluation in docs
            ],
        )
