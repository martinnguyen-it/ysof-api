import json
from typing import Optional
from fastapi import Depends, BackgroundTasks

from app.infra.security.security_service import generate_random_password, get_password_hash
from app.shared import request_object, use_case, response_object

from app.domain.admin.entity import Admin, AdminInCreate, AdminInDB, AdminInUpdateTime
from app.infra.admin.admin_repository import AdminRepository
from app.models.admin import AdminModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import Endpoint, AuditLogType
from app.shared.utils.general import get_current_season_value
from app.infra.tasks.email import (
    send_email_welcome_task,
    send_email_welcome_with_exist_account_task,
)


class CreateAdminRequestObject(request_object.ValidRequestObject):
    def __init__(self, current_admin: AdminModel, admin_in: AdminInCreate = None) -> None:
        self.admin_in = admin_in
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls, current_admin: AdminModel, payload: Optional[AdminInCreate] = None
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if not payload.email:
            invalid_req.add_error("payload.email", "Invalid email")

        if invalid_req.has_errors():
            return invalid_req

        return CreateAdminRequestObject(admin_in=payload, current_admin=current_admin)


class CreateAdminUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        admin_repository: AdminRepository = Depends(AdminRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.admin_repository = admin_repository
        self.audit_log_repository = audit_log_repository
        self.background_tasks = background_tasks

    def process_request(self, req_object: CreateAdminRequestObject):
        admin_in: AdminInCreate = req_object.admin_in
        existing_admin: Optional[AdminModel] = self.admin_repository.get_by_email(
            email=admin_in.email
        )

        current_season = get_current_season_value()
        if existing_admin:
            if existing_admin.latest_season == current_season:
                return response_object.ResponseFailure.build_parameters_error(
                    message="Email này đã tồn tại"
                )
            seasons = [*existing_admin.seasons, current_season]
            self.admin_repository.update(
                id=existing_admin.id,
                data=AdminInUpdateTime(
                    latest_season=current_season, seasons=seasons, roles=admin_in.roles
                ),
            )
            existing_admin.reload()
            send_email_welcome_with_exist_account_task.delay(
                email=existing_admin.email,
                season=current_season,
                full_name=existing_admin.full_name,
                is_admin=True,
            )
            return Admin(**AdminInDB.model_validate(existing_admin).model_dump())

        # password = "12345678"
        password = generate_random_password()
        obj_in: AdminInDB = AdminInDB(
            **admin_in.model_dump(exclude={"password"}),
            password=get_password_hash(password),
            latest_season=current_season,
            seasons=[current_season],
        )
        admin_in_db: AdminInDB = self.admin_repository.create(admin=obj_in)

        send_email_welcome_task.delay(
            email=admin_in_db.email,
            password=password,
            full_name=admin_in_db.full_name,
            is_admin=True,
        )

        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.CREATE,
                endpoint=Endpoint.ADMIN,
                season=current_season,
                author=req_object.current_admin,
                author_email=req_object.current_admin.email,
                author_name=req_object.current_admin.full_name,
                author_roles=req_object.current_admin.roles,
                description=json.dumps(
                    req_object.admin_in.model_dump(exclude_none=True),
                    default=str,
                    ensure_ascii=False,
                ),
            ),
        )

        return Admin(**admin_in_db.model_dump())
