from fastapi import Depends, BackgroundTasks
from app.shared import request_object, response_object, use_case
from app.domain.subject.entity import SubjectRegistrationInResponse
from app.infra.subject.subject_registration_repository import SubjectRegistrationRepository
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel
from app.models.student import StudentModel
from app.models.admin import AdminModel
from app.shared.utils.general import get_current_season_value
from app.infra.manage_form.manage_form_repository import ManageFormRepository
from app.models.manage_form import ManageFormModel
from app.domain.manage_form.enum import FormStatus, FormType
from app.infra.student.student_repository import StudentRepository
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
import json


class SubjectRegistrationStudentRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        subjects: list[str],
        current_student: StudentModel | str,
        current_admin: AdminModel | None = None,
    ):
        self.subjects = subjects
        self.current_student = current_student
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls,
        subjects: list[str],
        current_student: StudentModel | str,
        current_admin: AdminModel | None = None,
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not isinstance(subjects, list):
            invalid_req.add_error("subjects", "Invalid subjects list")

        if isinstance(current_student, str) and current_admin is None:
            invalid_req.add_error(
                "current_admin", "Current admin is required when student_id is provided"
            )

        if invalid_req.has_errors():
            return invalid_req

        return SubjectRegistrationStudentRequestObject(
            subjects=subjects, current_student=current_student, current_admin=current_admin
        )


class SubjectRegistrationStudentCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        manage_form_repository: ManageFormRepository = Depends(ManageFormRepository),
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        subject_registration_repository: SubjectRegistrationRepository = Depends(
            SubjectRegistrationRepository
        ),
        student_repository: StudentRepository = Depends(StudentRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.subject_registration_repository = subject_registration_repository
        self.subject_repository = subject_repository
        self.manage_form_repository = manage_form_repository
        self.student_repository = student_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: SubjectRegistrationStudentRequestObject):
        is_student_request = True
        if isinstance(req_object.current_student, str):
            is_student_request = False
            student = self.student_repository.get_by_id(req_object.current_student)
            if not student:
                return response_object.ResponseFailure.build_not_found_error(
                    message="Học viên không tồn tại"
                )
            req_object.current_student = student

        if is_student_request:
            form_subject_registration: ManageFormModel | None = (
                self.manage_form_repository.find_one({"type": FormType.SUBJECT_REGISTRATION})
            )

            if (
                not form_subject_registration
                or form_subject_registration.status == FormStatus.INACTIVE
            ):
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

        # Add audit log for admin processing
        if not is_student_request and req_object.current_admin:
            self.background_tasks.add_task(
                self.audit_log_repository.create,
                AuditLogInDB(
                    type=AuditLogType.UPDATE,
                    endpoint=Endpoint.STUDENT,
                    season=current_season,
                    author=req_object.current_admin,
                    author_email=req_object.current_admin.email,
                    author_name=req_object.current_admin.full_name,
                    author_roles=req_object.current_admin.roles,
                    description=json.dumps(
                        {
                            "action": "subject_registration_update",
                            "student_id": str(req_object.current_student.id),
                            "student_name": req_object.current_student.full_name,
                            "numerical_order": (
                                req_object.current_student.seasons_info[-1].numerical_order
                                if req_object.current_student.seasons_info
                                else "N/A"
                            ),
                            "subjects_registered": req_object.subjects,
                            "season": current_season,
                        },
                        default=str,
                        ensure_ascii=False,
                    ),
                ),
            )

        return SubjectRegistrationInResponse(
            student_id=str(req_object.current_student.id), subjects_registration=req_object.subjects
        )
