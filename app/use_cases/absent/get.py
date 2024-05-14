from bson import ObjectId
from fastapi import Depends
from app.shared import request_object, response_object, use_case
from app.domain.subject.entity import SubjectInDB
from app.models.student import StudentModel
from app.domain.lecturer.entity import LecturerInDB
from app.infra.absent.absent_repository import AbsentRepository
from app.models.absent import AbsentModel
from app.domain.absent.entity import AbsentInDB, AdminAbsentInResponse, StudentAbsentInResponse
from app.domain.student.entity import Student, StudentInDB
from app.infra.subject.subject_repository import SubjectRepository
from app.infra.student.student_repository import StudentRepository
from app.domain.subject.subject_evaluation.entity import LecturerInEvaluation, SubjectInEvaluation


class GetAbsentRequestObject(request_object.ValidRequestObject):
    def __init__(self, subject_id: str, current_student: StudentModel | str):
        self.current_student = current_student
        self.subject_id = subject_id

    @classmethod
    def builder(cls, subject_id: str, current_student: StudentModel | str) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not subject_id:
            invalid_req.add_error("subject_id", "Miss subject id")

        if invalid_req.has_errors():
            return invalid_req

        return GetAbsentRequestObject(subject_id=subject_id, current_student=current_student)


class GetAbsentUseCase(use_case.UseCase):
    def __init__(
        self,
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        student_repository: StudentRepository = Depends(StudentRepository),
        absent_repository: AbsentRepository = Depends(AbsentRepository),
    ):
        self.absent_repository = absent_repository
        self.subject_repository = subject_repository
        self.student_repository = student_repository

    def process_request(self, req_object: GetAbsentRequestObject):
        is_student_request = True
        if isinstance(req_object.current_student, str):
            is_student_request = False
            student = self.student_repository.get_by_id(req_object.current_student)
            if not student:
                return response_object.ResponseFailure.build_not_found_error(message="Học viên không tồn tại")
            req_object.current_student = student

        absent: AbsentModel = self.absent_repository.find_one(
            {"student": req_object.current_student.id, "subject": ObjectId(req_object.subject_id)}
        )
        if not absent:
            return response_object.ResponseFailure.build_not_found_error(message="Đơn nghỉ phép không tồn tại")

        return (
            StudentAbsentInResponse(
                **AbsentInDB.model_validate(absent).model_dump(exclude={"student", "subject"}),
                subject=SubjectInEvaluation(
                    **SubjectInDB.model_validate(absent.subject).model_dump(exclude=({"lecturer", "attachments"})),
                    lecturer=LecturerInEvaluation(**LecturerInDB.model_validate(absent.subject.lecturer).model_dump()),
                ),
            )
            if is_student_request
            else AdminAbsentInResponse(
                **AbsentInDB.model_validate(absent).model_dump(exclude={"student", "subject"}),
                subject=SubjectInEvaluation(
                    **SubjectInDB.model_validate(absent.subject).model_dump(exclude=({"lecturer", "attachments"})),
                    lecturer=LecturerInEvaluation(**LecturerInDB.model_validate(absent.subject.lecturer).model_dump()),
                ),
                student=Student(**StudentInDB.model_validate(absent.student).model_dump()),
            )
        )
