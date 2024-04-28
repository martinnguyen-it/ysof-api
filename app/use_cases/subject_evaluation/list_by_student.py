from fastapi import Depends
from app.shared import request_object, use_case, response_object
from app.domain.subject.entity import SubjectInDB
from app.models.student import StudentModel
from app.domain.subject.subject_evaluation.entity import (
    LecturerInEvaluation,
    StudentInEvaluation,
    SubjectEvaluationAdmin,
    SubjectEvaluationInDB,
    SubjectEvaluationStudent,
    SubjectInEvaluation,
)
from app.infra.subject.subject_evaluation_repository import SubjectEvaluationRepository
from app.domain.lecturer.entity import LecturerInDB
from app.models.subject_evaluation import SubjectEvaluationModel
from app.infra.student.student_repository import StudentRepository
from app.domain.student.entity import StudentInDB


class ListSubjectEvaluationByStudentRequestObject(request_object.ValidRequestObject):
    def __init__(self, current_student: StudentModel | str):
        self.current_student = current_student

    @classmethod
    def builder(cls, current_student: StudentModel | str) -> request_object.RequestObject:
        return ListSubjectEvaluationByStudentRequestObject(current_student=current_student)


class ListSubjectEvaluationByStudentUseCase(use_case.UseCase):
    def __init__(
        self,
        student_repository: StudentRepository = Depends(StudentRepository),
        subject_evaluation_repository: SubjectEvaluationRepository = Depends(SubjectEvaluationRepository),
    ):
        self.subject_evaluation_repository = subject_evaluation_repository
        self.student_repository = student_repository

    def process_request(self, req_object: ListSubjectEvaluationByStudentRequestObject):
        is_student_request = True
        if isinstance(req_object.current_student, str):
            is_student_request = False
            student = self.student_repository.get_by_id(req_object.current_student)
            if not student:
                return response_object.ResponseFailure.build_not_found_error(message="Học viên không tồn tại")
            req_object.current_student = student

        docs: SubjectEvaluationModel = self.subject_evaluation_repository.list(
            match_pipeline={"student": req_object.current_student.id}
        )
        return [
            (
                SubjectEvaluationStudent(
                    **SubjectEvaluationInDB.model_validate(subject_evaluation).model_dump(
                        exclude={"student", "subject"}
                    ),
                    subject=SubjectInEvaluation(
                        **SubjectInDB.model_validate(subject_evaluation.subject).model_dump(exclude=({"lecturer"})),
                        lecturer=LecturerInEvaluation(
                            **LecturerInDB.model_validate(subject_evaluation.subject.lecturer).model_dump()
                        ),
                    ),
                )
                if is_student_request
                else SubjectEvaluationAdmin(
                    **SubjectEvaluationInDB.model_validate(subject_evaluation).model_dump(
                        exclude={"student", "subject"}
                    ),
                    subject=SubjectInEvaluation(
                        **SubjectInDB.model_validate(subject_evaluation.subject).model_dump(exclude=({"lecturer"})),
                        lecturer=LecturerInEvaluation(
                            **LecturerInDB.model_validate(subject_evaluation.subject.lecturer).model_dump()
                        ),
                    ),
                    student=StudentInEvaluation(**StudentInDB.model_validate(student).model_dump()),
                )
            )
            for subject_evaluation in docs
        ]
