from fastapi import Depends
from app.shared import request_object, response_object, use_case
from app.domain.subject.entity import SubjectRegistrationInResponse
from app.infra.subject.subject_registration_repository import SubjectRegistrationRepository
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel
from app.models.student import StudentModel
from app.shared.utils.general import get_current_season_value
from app.infra.manage_form.manage_form_repository import ManageFormRepository
from app.models.manage_form import ManageFormModel
from app.domain.manage_form.enum import FormStatus, FormType


class SubjectRegistrationStudentRequestObject(request_object.ValidRequestObject):
    def __init__(self, subjects: list[str], current_student: StudentModel):
        self.subjects = subjects
        self.current_student = current_student

    @classmethod
    def builder(
        cls, subjects: list[str], current_student: StudentModel
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not isinstance(subjects, list):
            invalid_req.add_error("id", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return SubjectRegistrationStudentRequestObject(
            subjects=subjects, current_student=current_student
        )


class SubjectRegistrationStudentCase(use_case.UseCase):
    def __init__(
        self,
        manage_form_repository: ManageFormRepository = Depends(ManageFormRepository),
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        subject_registration_repository: SubjectRegistrationRepository = Depends(
            SubjectRegistrationRepository
        ),
    ):
        self.subject_registration_repository = subject_registration_repository
        self.subject_repository = subject_repository
        self.manage_form_repository = manage_form_repository

    def process_request(self, req_object: SubjectRegistrationStudentRequestObject):
        form_subject_registration: ManageFormModel | None = self.manage_form_repository.find_one(
            {"type": FormType.SUBJECT_REGISTRATION}
        )

        if not form_subject_registration or form_subject_registration.status == FormStatus.INACTIVE:
            return response_object.ResponseFailure.build_parameters_error(
                message="Form chưa được mở."
            )
        if form_subject_registration.status == FormStatus.CLOSED:
            return response_object.ResponseFailure.build_parameters_error(
                message="Form đã được đóng."
            )

        current_season: int = get_current_season_value()
        for subject_id in req_object.subjects:
            doc: SubjectModel | None = self.subject_repository.get_by_id(subject_id)
            if doc is None or doc.season != current_season:
                return response_object.ResponseFailure.build_not_found_error(
                    message="Môn học không tồn tại hoặc thuộc mùa cũ"
                )

        res = self.subject_registration_repository.delete_by_student_id(
            id=req_object.current_student.id
        )
        assert res, "Something went wrong"
        res = self.subject_registration_repository.insert_many(
            student_id=req_object.current_student.id, subject_ids=req_object.subjects
        )
        assert res, "Something went wrong"

        return SubjectRegistrationInResponse(
            student_id=str(req_object.current_student.id), subjects_registration=req_object.subjects
        )
