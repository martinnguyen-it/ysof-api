from fastapi import Depends, BackgroundTasks, HTTPException
import json
from mongoengine import NotUniqueError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import ValidationError

from app.domain.shared.enum import AccountStatus
from app.shared import request_object, use_case, response_object

from app.domain.student.entity import (
    AttentionImport,
    ErrorImport,
    ImportSpreadsheetsInResponse,
    ImportSpreadsheetsPayload,
    StudentInDB,
    StudentSeason,
)
from app.infra.student.student_repository import StudentRepository
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.models.admin import AdminModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.infra.security.security_service import get_password_hash
from app.infra.services.google_drive_api import GoogleDriveAPIService
from app.shared.utils.general import (
    convert_valid_date,
    copy_dict,
    extract_id_spreadsheet_from_url,
    get_current_season_value,
)
from app.shared.constant import HEADER_IMPORT_STUDENT
from app.domain.student.enum import FieldStudentEnum
from app.models.student import SeasonInfo, StudentModel
from app.infra.tasks.email import (
    send_email_welcome_task,
    send_email_welcome_with_exist_account_task,
)

LEN_HEADER_IMPORT_STUDENT = len(HEADER_IMPORT_STUDENT)


class ImportSpreadsheetsStudentRequestObject(request_object.ValidRequestObject):
    def __init__(self, current_admin: AdminModel, payload: ImportSpreadsheetsPayload) -> None:
        self.payload = payload
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls, current_admin: AdminModel, payload: ImportSpreadsheetsPayload
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not isinstance(payload.url, str):
            invalid_req.add_error("url", "Invalid url")

        if invalid_req.has_errors():
            return invalid_req

        return ImportSpreadsheetsStudentRequestObject(payload=payload, current_admin=current_admin)


class ImportSpreadsheetsStudentUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        student_repository: StudentRepository = Depends(StudentRepository),
        lecturer_repository: LecturerRepository = Depends(LecturerRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
        google_drive_service: GoogleDriveAPIService = Depends(GoogleDriveAPIService),
    ):
        self.student_repository = student_repository
        self.lecturer_repository = lecturer_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository
        self.google_drive_service = google_drive_service

    def get_data_from_spreadsheet(
        self,
        url: str,
        sheet_name: str,
    ) -> list[str]:
        id = extract_id_spreadsheet_from_url(url)
        creds = self.google_drive_service._creds
        try:
            service = build("sheets", "v4", credentials=creds)
            data = service.spreadsheets().values().get(spreadsheetId=id, range=sheet_name).execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise HTTPException(status_code=400, detail="Không tìm thấy spreadsheet hoặc sheet")
            elif e.resp.status == 403:
                raise HTTPException(status_code=400, detail="Không có quyền truy cập trang tính")
            else:
                raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {e}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {e}")

        return data["values"]

    def convert_value_spreadsheet_to_dict(self, data: list[str]) -> dict:
        return {
            HEADER_IMPORT_STUDENT[i]: data[i] if len(data) > i and data[i] else None
            for i in range(LEN_HEADER_IMPORT_STUDENT)
        }

    def process_request(self, req_object: ImportSpreadsheetsStudentRequestObject):
        data_import = self.get_data_from_spreadsheet(
            url=req_object.payload.url, sheet_name=req_object.payload.sheet_name
        )

        if HEADER_IMPORT_STUDENT != data_import.pop(0):
            return response_object.ResponseFailure.build_parameters_error(
                "Header của file import không hợp lệ"
            )

        updated: list[str] = []
        inserteds: list[str] = []
        errors: list[ErrorImport] = []
        attentions: list[AttentionImport] = []

        current_season = get_current_season_value()
        for idx, row in enumerate(data_import):
            data = self.convert_value_spreadsheet_to_dict(row)
            try:
                data_copy = copy_dict(data)
                seasons_info = StudentSeason(
                    season=current_season,
                    numerical_order=data_copy["numerical_order"],
                    group=data_copy["group"],
                )
                del data_copy["numerical_order"]
                del data_copy["group"]
                password = "12345678"
                # password = generate_random_password()
                student_in_db = StudentInDB(
                    **data_copy,
                    seasons_info=[seasons_info],
                    password=get_password_hash(password),
                )

                exist_std: StudentModel | None = self.student_repository.find_one(
                    {"email": student_in_db.email}
                )
                if exist_std:
                    attentions_message = ""
                    if exist_std.full_name != student_in_db.full_name:
                        attentions_message += (
                            f"Họ tên từ {exist_std.full_name} đã thay đổi "
                            + f"thành {student_in_db.full_name}"
                        )
                    if convert_valid_date(exist_std.date_of_birth) != student_in_db.date_of_birth:
                        attentions_message += ". " if attentions_message else ""
                        attentions_message += (
                            f"Ngày sinh từ {convert_valid_date(exist_std.date_of_birth)} "
                            + f"đã thay đổi thành {student_in_db.date_of_birth}"
                        )

                    exist_std.status = AccountStatus.ACTIVE

                    exist_std.seasons_info.append(
                        SeasonInfo(
                            numerical_order=seasons_info.numerical_order,
                            group=seasons_info.group,
                            season=seasons_info.season,
                        )
                    )

                    del data_copy["email"]
                    for key, value in data_copy.items():
                        if value is not None:
                            if hasattr(exist_std, key):
                                setattr(exist_std, key, value)

                    exist_std.save()
                    updated.append(exist_std.email)
                    if attentions_message:
                        attentions.append(AttentionImport(row=idx + 2, detail=attentions_message))

                    # send_email_welcome_with_exist_account_task.delay(
                    #     email=exist_std.email, season=current_season, full_name=exist_std.full_name
                    # )

                else:
                    inserted: StudentInDB = self.student_repository.create(student_in_db)
                    inserteds.append(inserted.email)

                    # send_email_welcome_task.delay(
                    #     email=student_in_db.email,
                    #     password=password,
                    #     full_name=student_in_db.full_name,
                    # )
            except NotUniqueError:
                errors.append(
                    ErrorImport(
                        row=idx + 2,
                        detail=f"Email đã tồn tại. ({data.get('email')})",
                    )
                )
            except ValidationError as e:
                errs = e.errors()
                message = [
                    (FieldStudentEnum[err["loc"][0]].value + ": " + err["msg"]) for err in errs
                ]
                message = "\n".join(message)
                errors.append(ErrorImport(row=idx + 2, detail=message))
            except Exception as e:
                errors.append(ErrorImport(row=idx + 2, detail=str(e)))

        response = ImportSpreadsheetsInResponse(
            errors=errors, inserteds=inserteds, updated=updated, attentions=attentions
        )
        if inserteds or attentions:
            self.background_tasks.add_task(
                self.audit_log_repository.create,
                AuditLogInDB(
                    type=AuditLogType.IMPORT,
                    endpoint=Endpoint.STUDENT,
                    season=current_season,
                    author=req_object.current_admin,
                    author_email=req_object.current_admin.email,
                    author_name=req_object.current_admin.full_name,
                    author_roles=req_object.current_admin.roles,
                    description=json.dumps(response, default=str, ensure_ascii=False),
                ),
            )

        return response
