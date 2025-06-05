import json
from fastapi import Depends, BackgroundTasks

from app.config import settings
from app.domain.upload.entity import AddPermissionDriveFile
from app.domain.upload.enum import RolePermissionGoogleEnum, TypePermissionGoogleEnum
from app.infra.tasks.drive_file import delete_file_drive_task
from app.shared import request_object, use_case, response_object

from app.domain.subject.entity import QuestionSpreadsheetResponse, SubjectInUpdateTime
from app.infra.subject.subject_repository import SubjectRepository
from app.models.admin import AdminModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.shared.utils.general import extract_id_spreadsheet_from_url, get_current_season_value
from app.infra.services.google_sheet_api import GoogleSheetAPIService
from app.domain.subject.enum import StatusSubjectEnum
from app.infra.services.google_drive_api import GoogleDriveAPIService


class GenerateQuestionSpreadsheetRequestObject(request_object.ValidRequestObject):
    def __init__(self, current_admin: AdminModel, subject_id: str) -> None:
        self.subject_id = subject_id
        self.current_admin = current_admin

    @classmethod
    def builder(cls, current_admin: AdminModel, subject_id: str) -> request_object.RequestObject:
        return GenerateQuestionSpreadsheetRequestObject(
            subject_id=subject_id, current_admin=current_admin
        )


class GenerateQuestionSpreadsheetUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        google_sheet_api_service: GoogleSheetAPIService = Depends(GoogleSheetAPIService),
        google_drive_api_service: GoogleDriveAPIService = Depends(GoogleDriveAPIService),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.subject_repository = subject_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository
        self.google_sheet_api_service = google_sheet_api_service
        self.google_drive_api_service = google_drive_api_service

    def process_request(self, req_object: GenerateQuestionSpreadsheetRequestObject):
        current_season = get_current_season_value()

        subject = self.subject_repository.get_by_id(req_object.subject_id)
        if subject is None:
            return response_object.ResponseFailure.build_not_found_error("Buổi học không tồn tại")

        if subject.season != current_season:
            return response_object.ResponseFailure.build_not_found_error(
                "Không thể tạo lại sheet câu hỏi của mùa cũ"
            )

        if subject.status != StatusSubjectEnum.INIT:
            return response_object.ResponseFailure.build_not_found_error(
                "Không thể tạo lại sheet câu hỏi đã gửi cho học viên"
            )

        if subject.question_url:
            old_question_id = extract_id_spreadsheet_from_url(subject.question_url)
            delete_file_drive_task.delay(old_question_id)

        file_id = extract_id_spreadsheet_from_url(
            "https://docs.google.com/spreadsheets/d/1OoEHe8eAePuaIymm34YPGyWgIp4g3MxYJBJ6ur-Qx-8/edit?usp=sharing"
        )
        response = self.google_sheet_api_service.duplicate_spreadsheet(
            source_spreadsheet_id=file_id,
            new_spreadsheet_name=subject.code + " - CÂU HỎI HỌC VIÊN",
        )
        self.google_sheet_api_service.update_cell_text(
            spreadsheet_id=response.id,
            sheet_name="Câu hỏi học viên",
            cell_range="C1",
            new_text="Chủ đề " + subject.code + " - " + subject.title,
        )

        lecturer = (
            (subject.lecturer.title + " " if subject.lecturer.title else "")
            + (subject.lecturer.holy_name + " " if subject.lecturer.holy_name else "")
            + (subject.lecturer.full_name)
        )
        self.google_sheet_api_service.update_cell_text(
            spreadsheet_id=response.id,
            sheet_name="Câu hỏi học viên",
            cell_range="C4",
            new_text="Giảng viên: " + lecturer,
        )
        permissions = [
            AddPermissionDriveFile(
                role=RolePermissionGoogleEnum.WRITER, type=TypePermissionGoogleEnum.ANYONE
            ),
        ]
        self.google_drive_api_service.add_multi_permissions(
            file_id=response.id, permissions=permissions
        )

        self.subject_repository.update(
            req_object.subject_id,
            SubjectInUpdateTime(
                question_url=f"https://docs.google.com/spreadsheets/d/{response.id}"
            ),
        )
        self.google_sheet_api_service.protect_range(
            spreadsheet_id=response.id,
            sheet_name="Câu hỏi học viên",
            cell_range="A1:B5",
            editors=[settings.YSOF_EMAIL, req_object.current_admin.email],
        )

        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.UPDATE,
                endpoint=Endpoint.SUBJECT,
                season=current_season,
                author=req_object.current_admin,
                author_email=req_object.current_admin.email,
                author_name=req_object.current_admin.full_name,
                author_roles=req_object.current_admin.roles,
                description=json.dumps(
                    {
                        "new_question_url": f"https://docs.google.com/spreadsheets/d/{response.id}",
                        "old_question_url": subject.question_url,
                    },
                    default=str,
                    ensure_ascii=False,
                ),
            ),
        )

        return QuestionSpreadsheetResponse(
            question_url=f"https://docs.google.com/spreadsheets/d/{response.id}"
        )
