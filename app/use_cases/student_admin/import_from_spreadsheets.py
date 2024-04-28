from fastapi import Depends, BackgroundTasks, HTTPException
import json
from mongoengine import NotUniqueError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import ValidationError

from app.shared import request_object, use_case, response_object

from app.domain.student.entity import ImportSpreadsheetsInResponse, ImportSpreadsheetsPayload, StudentInDB
from app.infra.student.student_repository import StudentRepository
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.models.admin import AdminModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.infra.security.security_service import get_password_hash
from app.infra.services.google_drive_api import GoogleDriveAPIService
from app.shared.utils.general import extract_id_spreadsheet_from_url, get_current_season_value
from app.shared.constant import HEADER_IMPORT_STUDENT
from app.domain.student.enum import FieldStudentEnum
from app.models.student import StudentModel
from app.infra.tasks.email import send_email_welcome_task

LEN_HEADER_IMPORT_STUDENT = len(HEADER_IMPORT_STUDENT)


class ImportSpreadsheetsStudentRequestObject(request_object.ValidRequestObject):
    def __init__(self, current_admin: AdminModel, payload: ImportSpreadsheetsPayload) -> None:
        self.payload = payload
        self.current_admin = current_admin

    @classmethod
    def builder(cls, current_admin: AdminModel, payload: ImportSpreadsheetsPayload) -> request_object.RequestObject:
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
                raise HTTPException(status_code=400, detail="Không có quyền truy cập")
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
            return response_object.ResponseFailure.build_parameters_error("Header của file import không hợp lệ")

        inserted_ids: list[str] = []
        errors: list = []

        current_season = get_current_season_value()
        for idx, row in enumerate(data_import):
            data = self.convert_value_spreadsheet_to_dict(row)
            try:
                password = "12345678"
                # password = generate_random_password()
                student_in_db = StudentInDB(
                    **data,
                    password=get_password_hash(password),
                    current_season=current_season,
                )

                exist_std: StudentModel | None = self.student_repository.find_one(
                    {"numerical_order": student_in_db.numerical_order}
                )
                if exist_std:
                    raise NotUniqueError

                inserted_id = self.student_repository.create(student_in_db).id
                inserted_ids.append(str(inserted_id))

                send_email_welcome_task.delay(
                    email=student_in_db.email, password=password, full_name=student_in_db.full_name
                )
            except NotUniqueError:
                errors.append({"row": idx + 2, "detail": "Email hoặc mshv đã tồn tại."})
            except ValidationError as e:
                errs = e.errors()
                message = [(FieldStudentEnum[err["loc"][0]].value + ": " + err["msg"]) for err in errs]
                message = "\n".join(message)
                errors.append({"row": idx + 2, "detail": message})
            except Exception as e:
                errors.append({"row": idx + 2, "detail": str(e)})

        if len(inserted_ids) > 0:
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
                    description=json.dumps(inserted_ids, default=str, ensure_ascii=False),
                ),
            )

        return ImportSpreadsheetsInResponse(errors=errors, inserted_ids=inserted_ids)
