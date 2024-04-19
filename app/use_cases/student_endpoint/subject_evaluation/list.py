from fastapi import Depends
from app.shared import request_object, use_case
from app.domain.subject.entity import SubjectInDB, SubjectInStudent
from app.models.student import StudentModel
from app.domain.subject.subject_evaluation.entity import SubjectEvaluation, SubjectEvaluationInDB
from app.infra.subject.subject_evaluation_repository import SubjectEvaluationRepository
from app.domain.lecturer.entity import LecturerInDB, LecturerInStudent
from app.models.subject_evaluation import SubjectEvaluationModel


class ListSubjectEvaluationRequestObject(request_object.ValidRequestObject):
    def __init__(self, current_student: StudentModel):
        self.current_student = current_student

    @classmethod
    def builder(cls, current_student: StudentModel) -> request_object.RequestObject:
        return ListSubjectEvaluationRequestObject(current_student=current_student)


class ListSubjectEvaluationUseCase(use_case.UseCase):
    def __init__(
        self,
        subject_evaluation_repository: SubjectEvaluationRepository = Depends(SubjectEvaluationRepository),
    ):
        self.subject_evaluation_repository = subject_evaluation_repository

    def process_request(self, req_object: ListSubjectEvaluationRequestObject):
        docs: SubjectEvaluationModel = self.subject_evaluation_repository.list(
            match_pipeline={"student": req_object.current_student.id}
        )
        return [
            SubjectEvaluation(
                **SubjectEvaluationInDB.model_validate(subject_evaluation).model_dump(exclude={"student", "subject"}),
                subject=SubjectInStudent(
                    **SubjectInDB.model_validate(subject_evaluation.subject).model_dump(exclude=({"lecturer"})),
                    lecturer=LecturerInStudent(
                        **LecturerInDB.model_validate(subject_evaluation.subject.lecturer).model_dump()
                    ),
                ),
            )
            for subject_evaluation in docs
        ]
