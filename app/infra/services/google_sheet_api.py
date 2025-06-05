from fastapi import Depends, HTTPException, BackgroundTasks
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.infra.services.google_drive_api import GoogleDriveAPIService
import logging
from app.domain.upload.enum import RolePermissionGoogleEnum, TypePermissionGoogleEnum
from app.domain.upload.entity import AddPermissionDriveFile, GoogleDriveAPIRes
from app.shared.utils.general import extract_id_spreadsheet_from_url

logger = logging.getLogger(__name__)


class GoogleSheetAPIService:
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        google_drive_api_service: GoogleDriveAPIService = Depends(GoogleDriveAPIService),
    ):
        self.google_drive_api_service = google_drive_api_service
        self.background_tasks = background_tasks
        self.service = build(
            "sheets", "v4", credentials=self.google_drive_api_service._creds
        ).spreadsheets()

    def create(self, name: str, email_owner: str):
        try:
            spreadsheet_meta = {"properties": {"title": name}}
            spreadsheet = self.service.create(body=spreadsheet_meta).execute()
        except HttpError as error:
            logger.error(f"An error occurred when create spreadsheet: {error}")
            raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")

        file_id = spreadsheet.get("spreadsheetId")

        file_info = self.google_drive_api_service.get(
            file_id=file_id, fields="id,mimeType,name,parents"
        )
        previous_parents = ",".join(file_info.get("parents"))
        self.google_drive_api_service.change_file_folder_parents(
            file_id=file_id, previous_parents=previous_parents
        )

        permissions = [
            AddPermissionDriveFile(
                email_address=email_owner,
                role=RolePermissionGoogleEnum.WRITER,
                type=TypePermissionGoogleEnum.USER,
            ),
            AddPermissionDriveFile(
                role=RolePermissionGoogleEnum.READER, type=TypePermissionGoogleEnum.ANYONE
            ),
        ]
        self.background_tasks.add_task(
            self.google_drive_api_service.add_multi_permissions, file_id, permissions
        )

        return GoogleDriveAPIRes.model_validate(file_info)

    def get_data_from_spreadsheet(self, url: str, sheet_name: str) -> list[str]:
        id = extract_id_spreadsheet_from_url(url)
        try:
            data = self.service.values().get(spreadsheetId=id, range=sheet_name).execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise HTTPException(status_code=400, detail="Không tìm thấy spreadsheet hoặc sheet")
            elif e.resp.status == 403:
                raise HTTPException(status_code=400, detail="Không có quyền truy cập trang tính")
            else:
                raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {e}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {e}")
        if "values" in data:
            return data["values"]
        return None

    def duplicate_spreadsheet(
        self,
        source_spreadsheet_id: str,
        new_spreadsheet_name: str,
        email_owner: str | None = None,
    ) -> GoogleDriveAPIRes:
        try:
            response = self.google_drive_api_service.duplicate_file(
                source_spreadsheet_id, new_spreadsheet_name
            )
            file_id = response.get("id")
            file_info = self.google_drive_api_service.get(
                file_id=file_id, fields="id,mimeType,name,parents"
            )
            previous_parents = ",".join(file_info.get("parents"))
            self.google_drive_api_service.change_file_folder_parents(
                file_id=file_id, previous_parents=previous_parents
            )

            if email_owner:
                self.google_drive_api_service.add_permission(
                    file_id=file_id,
                    type=TypePermissionGoogleEnum.USER,
                    role=RolePermissionGoogleEnum.WRITER,
                    email_address=email_owner,
                )

            return GoogleDriveAPIRes.model_validate(file_info)
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            raise HTTPException(status_code=400, detail=f"An error occurred: {error}")

    def update_cell_text(
        self, spreadsheet_id: str, sheet_name: str, cell_range: str, new_text: str
    ):
        try:
            self.service.values().update(
                spreadsheetId=spreadsheet_id,
                range=sheet_name + "!" + cell_range,
                valueInputOption="USER_ENTERED",
                body={"values": [[new_text]]},
            ).execute()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to update cell: {str(e)}")

    # Convert A1 notation to row and column indices (e.g., "C1" -> (1, 3))
    def _a1_to_rowcol(self, a1):
        col = 0
        for char in a1:
            if char.isalpha():
                col = col * 26 + (ord(char.upper()) - ord("A") + 1)
            else:
                row = int(a1[a1.index(char) :])
                break
        return row, col

    # Add a protected range to a sheet
    def protect_range(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        cell_range: str,
        description: str = "Protected Range",
        editors: list[str] | None = None,
    ):
        try:
            # Get the sheet ID for the specified sheet_name
            spreadsheet = self.service.get(spreadsheetId=spreadsheet_id).execute()
            sheet_id = None
            for sheet in spreadsheet.get("sheets", []):
                if sheet["properties"]["title"] == sheet_name:
                    sheet_id = sheet["properties"]["sheetId"]
                    break
            if sheet_id is None:
                raise ValueError(f"Sheet '{sheet_name}' not found in spreadsheet")

            # Convert A1 notation to grid range
            if ":" in cell_range:
                start_cell, end_cell = cell_range.split(":")
                start_row, start_col = self._a1_to_rowcol(start_cell)
                end_row, end_col = self._a1_to_rowcol(end_cell)
            else:
                start_row, start_col = self._a1_to_rowcol(cell_range)
                end_row, end_col = start_row, start_col

            # Define the protected range request
            protected_range = {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_row - 1,  # 0-based index
                    "endRowIndex": end_row,  # Exclusive
                    "startColumnIndex": start_col - 1,  # 0-based index
                    "endColumnIndex": end_col,  # Exclusive
                },
                "description": description,
                "requestingUserCanEdit": True,  # Allow the requesting user (service account) to edit
            }

            # Specify editors if provided
            if editors:
                protected_range["editors"] = {
                    "users": editors,  # List of email addresses
                    "domainUsersCanEdit": False,
                }

            # Create the batchUpdate request
            request = {"addProtectedRange": {"protectedRange": protected_range}}

            # Execute the request
            body = {"requests": [request]}
            self.service.batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        except HttpError as error:
            logger.error(f"An error occurred: {error.__dict__}")
            raise HTTPException(status_code=400, detail=f"An error occurred: {error}")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise HTTPException(status_code=400, detail=f"An error occurred: {e}")
