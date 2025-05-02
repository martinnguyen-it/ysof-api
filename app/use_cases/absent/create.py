from fastapi import Depends, BackgroundTasks
import json
from mongoengine import NotUniqueError
from app.domain.absent.enum import AbsentType, CreatedByEnum
from app.infra.subject.subject_registration_repository import SubjectRegistrationRepository
from app.shared import request_object, response_object, use_case
from app.domain.subject.entity import SubjectInDB
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel
from app.models.student import StudentModel
from app.shared.utils.general import get_current_season_value
from app.infra.manage_form.manage_form_repository import ManageFormRepository
from app.models.manage_form import ManageFormModel
from app.domain.manage_form.enum import FormStatus, FormType
from app.domain.absent.entity import AbsentInDB, AdminAbsentInResponse, StudentAbsentInResponse
from app.infra.absent.absent_repository import AbsentRepository
from app.domain.manage_form.entity import ManageFormEvaluationOrAbsent
from app.domain.lecturer.entity import LecturerInDB
from app.models.absent import AbsentModel
from app.domain.student.entity import Student, StudentInDB
from app.infra.student.student_repository import StudentRepository
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.models.admin import AdminModel
from app.domain.subject.subject_evaluation.entity import LecturerInEvaluation, SubjectInEvaluation


class CreateAbsentRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        subject_id: str,
        type: AbsentType,
        current_student: StudentModel | str,
        reason: str | None,
        note: str | None,
        current_admin: AdminModel | None = None,
    ):
        self.current_student = current_student
        self.subject_id = subject_id
        self.reason = reason
        self.note = note
        self.current_admin = current_admin
        self.type = type

    @classmethod
    def builder(
        cls,
        subject_id: str,
        current_student: StudentModel | str,
        reason: str | None = None,
        note: str | None = None,
        current_admin: AdminModel | None = None,
        type: AbsentType = AbsentType.NO_ATTEND,
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not subject_id:
            invalid_req.add_error("subject_id", "Miss subject id")

        if isinstance(current_student, str) and current_admin is None:
            invalid_req.add_error("current_admin", "Current admin is required")

        if invalid_req.has_errors():
            return invalid_req

        return CreateAbsentRequestObject(
            subject_id=subject_id,
            current_student=current_student,
            reason=reason,
            note=note,
            current_admin=current_admin,
            type=type,
        )


class CreateAbsentUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        manage_form_repository: ManageFormRepository = Depends(ManageFormRepository),
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        student_repository: StudentRepository = Depends(StudentRepository),
        subject_registration_repository: SubjectRegistrationRepository = Depends(
            SubjectRegistrationRepository
        ),
        absent_repository: AbsentRepository = Depends(AbsentRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.absent_repository = absent_repository
        self.subject_repository = subject_repository
        self.manage_form_repository = manage_form_repository
        self.student_repository = student_repository
        self.subject_registration_repository = subject_registration_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: CreateAbsentRequestObject):
        is_student_request = True
        if isinstance(req_object.current_student, str):
            is_student_request = False
            student = self.student_repository.get_by_id(req_object.current_student)
            if not student:
                return response_object.ResponseFailure.build_not_found_error(
                    message="Học viên không tồn tại"
                )
            req_object.current_student = student

        current_season: int = get_current_season_value()
        subject: SubjectModel | None = self.subject_repository.get_by_id(req_object.subject_id)
        if subject is None or subject.season != current_season:
            return response_object.ResponseFailure.build_not_found_error(
                message="Môn học không tồn tại hoặc thuộc mùa cũ."
            )

        subject_registration = self.subject_registration_repository.find_one(
            {"subject": subject.id, "student": req_object.current_student.id},
        )

        if subject_registration is None:
            return response_object.ResponseFailure.build_not_found_error(
                message="Học viên không đăng ký môn học này."
            )

        if is_student_request:
            form_absent: ManageFormModel | None = self.manage_form_repository.find_one(
                {"type": FormType.SUBJECT_ABSENT}
            )
            if not form_absent or form_absent.status == FormStatus.INACTIVE:
                return response_object.ResponseFailure.build_parameters_error(
                    message="Form chưa được mở."
                )
            if form_absent.status == FormStatus.CLOSED:
                return response_object.ResponseFailure.build_parameters_error(
                    message="Form đã được đóng."
                )
            form_absent: ManageFormEvaluationOrAbsent = ManageFormEvaluationOrAbsent.model_validate(
                form_absent
            )
            if req_object.subject_id != form_absent.data.subject_id:
                return response_object.ResponseFailure.build_parameters_error(
                    message="Form hiện tại không mở cho môn học này."
                )

        try:
            absent: AbsentModel = self.absent_repository.create(
                AbsentInDB(
                    student=req_object.current_student,
                    subject=subject,
                    type=req_object.type,
                    reason=req_object.reason,
                    note=req_object.note,
                    created_by=CreatedByEnum.HV if is_student_request else CreatedByEnum.BTC,
                )
            )
            if not is_student_request:
                self.background_tasks.add_task(
                    self.audit_log_repository.create,
                    AuditLogInDB(
                        type=AuditLogType.CREATE,
                        endpoint=Endpoint.ABSENT,
                        season=current_season,
                        author=req_object.current_admin,
                        author_email=req_object.current_admin.email,
                        author_name=req_object.current_admin.full_name,
                        author_roles=req_object.current_admin.roles,
                        description=json.dumps(
                            {
                                "student_id": req_object.current_student.id,
                                "subject_id": req_object.subject_id,
                                "reason": req_object.reason,
                                "note": req_object.note,
                            },
                            default=str,
                            ensure_ascii=False,
                        ),
                    ),
                )
        except NotUniqueError:
            return response_object.ResponseFailure.build_parameters_error(
                "Đơn nghỉ phép đã được tạo trước đây."
            )
        except Exception:
            return response_object.ResponseFailure.build_system_error("Something went wrong")

        return (
            StudentAbsentInResponse(
                **AbsentInDB.model_validate(absent).model_dump(exclude={"student", "subject"}),
                subject=SubjectInEvaluation(
                    **SubjectInDB.model_validate(absent.subject).model_dump(exclude=({"lecturer"})),
                    lecturer=LecturerInEvaluation(
                        **LecturerInDB.model_validate(absent.subject.lecturer).model_dump()
                    ),
                ),
            )
            if is_student_request
            else AdminAbsentInResponse(
                **AbsentInDB.model_validate(absent).model_dump(exclude={"student", "subject"}),
                subject=SubjectInEvaluation(
                    **SubjectInDB.model_validate(absent.subject).model_dump(exclude=({"lecturer"})),
                    lecturer=LecturerInEvaluation(
                        **LecturerInDB.model_validate(absent.subject.lecturer).model_dump()
                    ),
                ),
                student=Student(**StudentInDB.model_validate(absent.student).model_dump()),
            )
        )
