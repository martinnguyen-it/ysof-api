from typing import Optional
from fastapi import Depends, BackgroundTasks


from app.domain.rolll_call.entity import RollCallBulkSheet
from app.domain.subject.enum import StatusSubjectEnum
from app.infra.roll_call.roll_call_repository import RollCallRepository
from app.infra.services.google_sheet_api import GoogleSheetAPIService
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel
from app.shared import request_object, use_case, response_object

from app.infra.student.student_repository import StudentRepository
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.models.admin import AdminModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.shared.utils.general import (
    get_current_season_value,
)


HEADER_BULK_ROLL_CALL = ["MSHV"]


class RollCallBySheetRequestObject(request_object.ValidRequestObject):
    def __init__(self, current_admin: AdminModel, payload: RollCallBulkSheet) -> None:
        self.payload = payload
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls, current_admin: AdminModel, payload: RollCallBulkSheet
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not isinstance(payload.url, str):
            invalid_req.add_error("url", "Invalid url")

        if invalid_req.has_errors():
            return invalid_req

        return RollCallBySheetRequestObject(payload=payload, current_admin=current_admin)


class RollCallBySheetUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        student_repository: StudentRepository = Depends(StudentRepository),
        roll_call_repository: RollCallRepository = Depends(RollCallRepository),
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        lecturer_repository: LecturerRepository = Depends(LecturerRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
        google_sheet_api_service: GoogleSheetAPIService = Depends(GoogleSheetAPIService),
    ):
        self.roll_call_repository = roll_call_repository
        self.student_repository = student_repository
        self.subject_repository = subject_repository
        self.lecturer_repository = lecturer_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository
        self.google_sheet_api_service = google_sheet_api_service

    def process_request(self, req_object: RollCallBySheetRequestObject):
        current_season = get_current_season_value()
        subject: Optional[SubjectModel] = self.subject_repository.get_by_id(
            req_object.payload.subject_id
        )
        if not subject:
            return response_object.ResponseFailure.build_not_found_error("Môn học không tồn tại")
        if subject.season != current_season:
            return response_object.ResponseFailure.build_parameters_error(
                "Môn học không thuộc mùa hiện tại"
            )
        if subject.status not in [StatusSubjectEnum.COMPLETED, StatusSubjectEnum.CLOSE_EVALUATION]:
            return response_object.ResponseFailure.build_parameters_error(
                "Môn học chưa đủ điều kiện để thực hiện điểm danh"
            )

        data_import = self.google_sheet_api_service.get_data_from_spreadsheet(
            url=req_object.payload.url,
            sheet_name=req_object.payload.sheet_name,
        )
        if not data_import or len(data_import) < 2:
            return response_object.ResponseFailure.build_parameters_error(
                "File import không hợp lệ hoặc không có dữ liệu"
            )

        if HEADER_BULK_ROLL_CALL != data_import.pop(0):
            return response_object.ResponseFailure.build_parameters_error(
                "Header của file import không hợp lệ"
            )

        numerical_orders = set()
        for idx, row in enumerate(data_import):
            try:
                if len(row) != 0:
                    numerical_orders.add(int(row[0]))
            except ValueError:
                return response_object.ResponseFailure.build_parameters_error(
                    f"MSHV không hợp lệ - hàng số {idx + 2}"
                )

        self.roll_call_repository.update_bulk(
            numerical_orders=numerical_orders,
            subject=subject,
            current_season=current_season,
        )
        return True
