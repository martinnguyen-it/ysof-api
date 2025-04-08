import json
from fastapi import BackgroundTasks, Depends
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.models.admin import AdminModel
from app.shared import request_object, response_object, use_case
from app.infra.celery_result.celery_result_repository import CeleryResultRepository
from app.shared.utils.general import get_current_season_value


class MarkResolvedFailedRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        task_ids: list[str],
        current_admin: AdminModel,
        is_undo: bool = False,
    ):
        self.task_ids = task_ids
        self.current_admin = current_admin
        self.is_undo = is_undo

    @classmethod
    def builder(cls, task_ids: list[str], current_admin: AdminModel, is_undo: bool = False):
        return MarkResolvedFailedRequestObject(
            task_ids=task_ids, current_admin=current_admin, is_undo=is_undo
        )


class MarkResolvedFailedUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        celery_result_repository: CeleryResultRepository = Depends(CeleryResultRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.celery_result_repository = celery_result_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: MarkResolvedFailedRequestObject):
        count = self.celery_result_repository.count_list(
            match_pipeline={
                "task_id": {"$in": req_object.task_ids},
                "resolved": True if req_object.is_undo else {"$ne": True},
            }
        )
        if count != len(req_object.task_ids):
            return response_object.ResponseFailure.build_parameters_error(
                "Task IDs đã được xử lý hoặc không tồn tại"
            )

        res = self.celery_result_repository.mark_resolved_failed(
            req_object.task_ids, is_undo=req_object.is_undo
        )

        if not res:
            raise Exception("Something went wrong")

        current_season: int = get_current_season_value()
        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.UPDATE,
                endpoint=Endpoint.CELERY_RESULT,
                season=current_season,
                author=req_object.current_admin,
                author_email=req_object.current_admin.email,
                author_name=req_object.current_admin.full_name,
                author_roles=req_object.current_admin.roles,
                description=json.dumps(
                    {"task_ids": req_object.task_ids, "is_undo": req_object.is_undo},
                    default=str,
                    ensure_ascii=False,
                ),
            ),
        )
        return {"success": True}
