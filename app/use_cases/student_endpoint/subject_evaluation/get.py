from bson import ObjectId
from fastapi import Depends
from app.shared import request_object, response_object, use_case
from app.domain.subject.entity import SubjectInDB, SubjectInStudent
from app.models.student import StudentModel
from app.domain.subject.subject_evaluation.entity import SubjectEvaluation, SubjectEvaluationInDB
from app.infra.subject.subject_evaluation_repository import SubjectEvaluationRepository
from app.domain.lecturer.entity import LecturerInDB, LecturerInStudent
from app.models.subject_evaluation import SubjectEvaluationModel


class GetSubjectEvaluationRequestObject(request_object.ValidRequestObject):
    def __init__(self, subject_id: str, current_student: StudentModel):
        self.current_student = current_student
        self.subject_id = subject_id

    @classmethod
    def builder(cls, subject_id: str, current_student: StudentModel) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not subject_id:
            invalid_req.add_error("subject_id", "Miss subject id")

        if invalid_req.has_errors():
            return invalid_req

        return GetSubjectEvaluationRequestObject(subject_id=subject_id, current_student=current_student)


class GetSubjectEvaluationUseCase(use_case.UseCase):
    def __init__(
        self,
        subject_evaluation_repository: SubjectEvaluationRepository = Depends(SubjectEvaluationRepository),
    ):
        self.subject_evaluation_repository = subject_evaluation_repository

    def process_request(self, req_object: GetSubjectEvaluationRequestObject):
        subject_evaluation: SubjectEvaluationModel = self.subject_evaluation_repository.find_one(
            {"student": req_object.current_student.id, "subject": ObjectId(req_object.subject_id)}
        )
        if not subject_evaluation:
            return response_object.ResponseFailure.build_not_found_error(message="Lượng giá không tồn tại")

        return SubjectEvaluation(
            **SubjectEvaluationInDB.model_validate(subject_evaluation).model_dump(exclude={"student", "subject"}),
            subject=SubjectInStudent(
                **SubjectInDB.model_validate(subject_evaluation.subject).model_dump(exclude=({"lecturer"})),
                lecturer=LecturerInStudent(
                    **LecturerInDB.model_validate(subject_evaluation.subject.lecturer).model_dump()
                ),
            ),
        )
