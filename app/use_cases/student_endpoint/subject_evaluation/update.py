from fastapi import Depends
from bson import ObjectId
from app.shared import request_object, response_object, use_case
from app.domain.subject.entity import SubjectInDB
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel
from app.models.student import StudentModel
from app.shared.utils.general import get_current_season_value
from app.infra.manage_form.manage_form_repository import ManageFormRepository
from app.models.manage_form import ManageFormModel
from app.domain.manage_form.enum import FormStatus, FormType
from app.domain.subject.subject_evaluation.entity import (
    LecturerInEvaluation,
    SubjectEvaluationInDB,
    SubjectEvaluationInUpdate,
    SubjectEvaluationInUpdateTime,
    SubjectEvaluationStudent,
    SubjectInEvaluation,
)
from app.infra.subject.subject_evaluation_repository import SubjectEvaluationRepository
from app.domain.manage_form.entity import ManageFormEvaluationOrAbsent
from app.domain.lecturer.entity import LecturerInDB
from app.models.subject_evaluation import SubjectEvaluationModel, SubjectEvaluationQuestionModel
from app.infra.subject.subject_evaluation_question_repository import SubjectEvaluationQuestionRepository


class UpdateSubjectEvaluationRequestObject(request_object.ValidRequestObject):
    def __init__(self, subject_id: str, payload: SubjectEvaluationInUpdate, current_student: StudentModel):
        self.current_student = current_student
        self.subject_id = subject_id
        self.payload = payload

    @classmethod
    def builder(
        cls, subject_id: str, payload: SubjectEvaluationInUpdate, current_student: StudentModel
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not subject_id:
            invalid_req.add_error("subject_id", "Miss subject id")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateSubjectEvaluationRequestObject(
            subject_id=subject_id, payload=payload, current_student=current_student
        )


class UpdateSubjectEvaluationUseCase(use_case.UseCase):
    def __init__(
        self,
        manage_form_repository: ManageFormRepository = Depends(ManageFormRepository),
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        subject_evaluation_question_repository: SubjectEvaluationQuestionRepository = Depends(
            SubjectEvaluationQuestionRepository
        ),
        subject_evaluation_repository: SubjectEvaluationRepository = Depends(SubjectEvaluationRepository),
    ):
        self.subject_evaluation_repository = subject_evaluation_repository
        self.subject_repository = subject_repository
        self.manage_form_repository = manage_form_repository
        self.subject_evaluation_question_repository = subject_evaluation_question_repository

    def process_request(self, req_object: UpdateSubjectEvaluationRequestObject):
        current_season: int = get_current_season_value()
        subject: SubjectModel | None = self.subject_repository.get_by_id(req_object.subject_id)
        if subject is None or subject.season != current_season:
            return response_object.ResponseFailure.build_not_found_error(
                message="Môn học không tồn tại hoặc thuộc mùa cũ."
            )

        subject_evaluation: SubjectEvaluationModel = self.subject_evaluation_repository.find_one(
            {"student": req_object.current_student.id, "subject": ObjectId(req_object.subject_id)}
        )
        if not subject_evaluation:
            return response_object.ResponseFailure.build_not_found_error(message="Lượng giá không tồn tại")

        form_subject_evaluation: ManageFormModel | None = self.manage_form_repository.find_one(
            {"type": FormType.SUBJECT_EVALUATION}
        )
        if not form_subject_evaluation or form_subject_evaluation.status == FormStatus.INACTIVE:
            return response_object.ResponseFailure.build_system_error(message="Form chưa được mở.")
        if form_subject_evaluation.status == FormStatus.CLOSED:
            return response_object.ResponseFailure.build_system_error(message="Form đã được đóng.")

        form_subject_evaluation: ManageFormEvaluationOrAbsent = ManageFormEvaluationOrAbsent.model_validate(
            form_subject_evaluation
        )
        if req_object.subject_id != form_subject_evaluation.data.subject_id:
            return response_object.ResponseFailure.build_parameters_error(
                message="Form hiện tại không mở cho môn học này."
            )

        if req_object.payload.answers:
            subject_evaluation_question: SubjectEvaluationQuestionModel = (
                self.subject_evaluation_question_repository.get_by_subject_id(subject_id=req_object.subject_id)
            )
            if not subject_evaluation_question:
                return response_object.ResponseFailure.build_not_found_error(
                    message="Câu hỏi lượng giá chưa được thêm."
                )

            if len(req_object.payload.answers) != len(subject_evaluation_question.questions):
                return response_object.ResponseFailure.build_parameters_error("Câu trả lời không hợp lệ.")

        self.subject_evaluation_repository.update(
            id=subject_evaluation.id, data=SubjectEvaluationInUpdateTime(**req_object.payload.model_dump())
        )
        subject_evaluation.reload()

        return SubjectEvaluationStudent(
            **SubjectEvaluationInDB.model_validate(subject_evaluation).model_dump(exclude={"student", "subject"}),
            subject=SubjectInEvaluation(
                **SubjectInDB.model_validate(subject_evaluation.subject).model_dump(exclude=({"lecturer"})),
                lecturer=LecturerInEvaluation(
                    **LecturerInDB.model_validate(subject_evaluation.subject.lecturer).model_dump()
                ),
            ),
        )
