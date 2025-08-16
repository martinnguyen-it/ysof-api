import json
from typing import Optional
from fastapi import Depends, BackgroundTasks

from app.domain.shared.enum import AccountStatus
from app.infra.tasks.email import (
    send_email_welcome_task,
    send_email_welcome_with_exist_account_task,
)
from app.models.student import SeasonInfo, StudentModel
from app.shared import request_object, use_case, response_object

from app.domain.student.entity import Student, StudentInCreate, StudentInDB, StudentSeason
from app.infra.student.student_repository import StudentRepository
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.models.admin import AdminModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.infra.security.security_service import generate_random_password, get_password_hash
from app.shared.common_exception import CustomException
from app.shared.utils.general import get_current_season_value


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
        current_season = get_current_season_value()

        existing_student: Optional[StudentModel] = self.student_repository.find_one(
            {"email": req_object.student_in.email}
        )

        seasons_info = StudentSeason(
            season=current_season,
            numerical_order=req_object.student_in.numerical_order,
            group=req_object.student_in.group,
        )
        student: StudentInDB | None = None
        if existing_student:
            existing_student.seasons_info.append(
                SeasonInfo(
                    numerical_order=seasons_info.numerical_order,
                    group=seasons_info.group,
                    season=seasons_info.season,
                )
            )

            for key, value in req_object.student_in.model_dump(exclude={"email"}).items():
                if value is not None:
                    if hasattr(existing_student, key):
                        setattr(existing_student, key, value)

            existing_student.status = AccountStatus.ACTIVE

            try:
                existing_student.save()
                student = StudentInDB.model_validate(existing_student)
            except CustomException as e:
                return response_object.ResponseFailure.build_parameters_error(message=str(e))
            except Exception as e:
                raise e

            send_email_welcome_with_exist_account_task.delay(
                email=student.email, season=current_season, full_name=student.full_name
            )

        else:
            # password = "12345678"
            password = generate_random_password()

            obj_in: StudentInDB = StudentInDB(
                **req_object.student_in.model_dump(exclude={"numerical_order", "group"}),
                seasons_info=[seasons_info],
                password=get_password_hash(password),
            )

            try:
                student: StudentInDB = self.student_repository.create(student=obj_in)
            except CustomException as e:
                return response_object.ResponseFailure.build_parameters_error(message=str(e))
            except Exception as e:
                raise e

            send_email_welcome_task.delay(
                email=student.email, password=password, full_name=student.full_name
            )

        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.UPDATE if existing_student else AuditLogType.CREATE,
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
