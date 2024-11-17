import json
from typing import Optional
from fastapi import Depends, BackgroundTasks
from mongoengine import NotUniqueError

from app.models.student import StudentModel
from app.shared import request_object, use_case, response_object

from app.domain.student.entity import Student, StudentInCreate, StudentInDB
from app.infra.student.student_repository import StudentRepository
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.models.admin import AdminModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.infra.security.security_service import get_password_hash
from app.shared.utils.general import get_current_season_value
from app.infra.tasks.email import send_email_welcome_task


class CreateStudentRequestObject(request_object.ValidRequestObject):
    def __init__(self, current_admin: AdminModel, student_in: StudentInCreate) -> None:
        self.student_in = student_in
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls, current_admin: AdminModel, payload: Optional[StudentInCreate] = None
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return CreateStudentRequestObject(student_in=payload, current_admin=current_admin)


class CreateStudentUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        student_repository: StudentRepository = Depends(StudentRepository),
        lecturer_repository: LecturerRepository = Depends(LecturerRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.student_repository = student_repository
        self.lecturer_repository = lecturer_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: CreateStudentRequestObject):
        existing_student: Optional[StudentModel] = self.student_repository.find_one(
            {
                "$or": [
                    {"email": req_object.student_in.email},
                    {"numerical_order": req_object.student_in.numerical_order},
                ]
            }
        )

        if existing_student:
            return response_object.ResponseFailure.build_parameters_error(
                message="Email hoặc mshv đã tồn tại"
            )

        password = "12345678"
        # password = generate_random_password()
        current_season = get_current_season_value()
        obj_in: StudentInDB = StudentInDB(
            **req_object.student_in.model_dump(),
            password=get_password_hash(password),
            latest_season=current_season,
        )

        try:
            student: StudentInDB = self.student_repository.create(student=obj_in)
        except NotUniqueError as e:
            raise e
        except Exception:
            return response_object.ResponseFailure.build_system_error("Something went wrong")

        send_email_welcome_task.delay(
            email=student.email, password=password, full_name=student.full_name
        )

        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.CREATE,
                endpoint=Endpoint.STUDENT,
                season=current_season,
                author=req_object.current_admin,
                author_email=req_object.current_admin.email,
                author_name=req_object.current_admin.full_name,
                author_roles=req_object.current_admin.roles,
                description=json.dumps(
                    req_object.student_in.model_dump(exclude_none=True),
                    default=str,
                    ensure_ascii=False,
                ),
            ),
        )

        return Student(**student.model_dump())
