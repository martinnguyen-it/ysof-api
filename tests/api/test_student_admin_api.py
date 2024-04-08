import app.interfaces.api_v1
import app.interfaces.api_v1.admin
import time
import unittest
from unittest.mock import patch
from mongoengine import connect, disconnect
from fastapi.testclient import TestClient
from app.main import app
import mongomock
from google.oauth2.credentials import Credentials

from app.models.student import StudentModel
from app.models.admin import AdminModel
from app.infra.security.security_service import get_password_hash, TokenData, verify_password
from app.models.season import SeasonModel
from app.models.audit_log import AuditLogModel
from app.domain.audit_log.enum import AuditLogType, Endpoint


class TestUserApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect()
        connect("mongoenginetest", host="mongodb://localhost:1234", mongo_client_class=mongomock.MongoClient)
        cls.client = TestClient(app)
        cls.season: SeasonModel = SeasonModel(
            title="CÙNG GIÁO HỘI, NGƯỜI TRẺ BƯỚC ĐI TRONG HY VỌNG", academic_year="2023-2024", season=3, is_current=True
        ).save()
        cls.admin: AdminModel = AdminModel(
            status="active",
            roles=[
                "admin",
            ],
            holy_name="Martin",
            phone_number=["0123456789"],
            current_season=2,
            seasons=[2],
            email="admin@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.admin2: AdminModel = AdminModel(
            status="active",
            roles=[
                "bkl",
            ],
            holy_name="Martin",
            phone_number=["0123456789"],
            current_season=2,
            seasons=[2],
            email="admin2@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.student: StudentModel = StudentModel(
            numerical_order=1,
            group=2,
            status="active",
            holy_name="Martin",
            phone_number="0123456789",
            current_season=3,
            email="student@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.student2: StudentModel = StudentModel(
            numerical_order=2,
            group=2,
            status="active",
            holy_name="Martin",
            phone_number="0123456789",
            current_season=3,
            email="student2@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.student3: StudentModel = StudentModel(
            numerical_order=3,
            group=2,
            status="active",
            holy_name="Martin",
            phone_number="0123456789",
            current_season=3,
            email="student4@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    def test_create_student(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_email = "student3@example.com"

            mock_token.return_value = TokenData(email=self.admin2.email)
            r = self.client.post(
                "/api/v1/admin/students",
                json={
                    "numerical_order": 10,
                    "group": 10,
                    "holy_name": "string",
                    "full_name": "string",
                    "email": mock_email,
                    "sex": "Nam",
                    "date_of_birth": "2024-04-06",
                    "origin_address": "string",
                    "diocese": "string",
                    "phone_number": "string",
                    "avatar": "string",
                    "education": "string",
                    "job": "string",
                    "note": "string",
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 403

            mock_token.return_value = TokenData(email=self.admin.email)
            r = self.client.post(
                "/api/v1/admin/students",
                json={
                    "numerical_order": 10,
                    "group": 10,
                    "holy_name": "string",
                    "full_name": "string",
                    "email": mock_email,
                    "sex": "Nam",
                    "date_of_birth": "2024-04-06",
                    "origin_address": "string",
                    "diocese": "string",
                    "phone_number": "string",
                    "avatar": "string",
                    "education": "string",
                    "job": "string",
                    "note": "string",
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            student: StudentModel = StudentModel.objects(id=r.json().get("id")).get()
            assert "password" not in r.json()
            assert student.email == mock_email
            assert student.created_at
            assert student.updated_at
            assert student.password

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find({"type": AuditLogType.CREATE, "endpoint": Endpoint.STUDENT})
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1

    def test_get_student_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.admin.email)
            r = self.client.get(
                f"/api/v1/admin/students/{self.student.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp.get("full_name") == self.student.full_name
            assert resp.get("email") == self.student.email

    def test_get_all_students(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.admin.email)
            r = self.client.get(
                "/api/v1/admin/students",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["pagination"]["total"] == 3

    def test_update_student_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.admin.email)
            r = self.client.put(
                f"/api/v1/admin/students/{self.student.id}",
                json={"full_name": "Updated"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            doc: StudentModel = StudentModel.objects(id=r.json().get("id")).get()
            assert doc.full_name == "Updated"

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find({"type": AuditLogType.UPDATE, "endpoint": Endpoint.STUDENT})
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 2

    def test_delete_student_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.admin.email)
            r = self.client.delete(
                f"/api/v1/admin/students/{self.student2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200

            r = self.client.get(
                f"/api/v1/admin/students/{self.student2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 404

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find({"type": AuditLogType.DELETE, "endpoint": Endpoint.STUDENT})
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1

    def test_import_student_from_spreadsheet(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token, patch(
            "app.use_cases.student_admin.import_from_spreadsheets.ImportSpreadsheetsStudentUseCase.get_data_from_spreadsheet"
        ) as mock_get_data_spreadsheet, patch(
            "app.infra.services.google_drive_api.GoogleDriveApiService._get_oauth_token"
        ) as mock_get_oauth_token:
            mock_token.return_value = TokenData(email=self.admin.email)
            mock_get_oauth_token.return_value = Credentials(
                token="<access_token>",
                refresh_token="<refresh_token>",
                client_id="<client_id>",
                client_secret="<client_secret>",
                token_uri="<token_uri>",
                scopes=["https://www.googleapis.com/auth/drive"],
            )
            mock_get_data_spreadsheet.return_value = [
                [
                    "numerical_order",
                    "group",
                    "holy_name",
                    "full_name",
                    "sex",
                    "date_of_birth",
                    "origin_address",
                    "diocese",
                    "email",
                    "phone_number",
                    "education",
                    "job",
                    "note",
                ],
                [
                    "1",
                    "1",
                    "Gioan",
                    "Trần Văn Khải",
                    "Nam",
                    "21/04/2001",
                    "Hà Nội",
                    "Hà Tĩnh",
                    "khai26434@gmail.com",
                    "0913741084",
                    "Cấp 3",
                    "Học sinh/Sinh viên",
                ],
                [
                    "7",
                    "1",
                    "Teresa",
                    "Trần Thị Kim Oanh",
                    "Nữ",
                    "28/04/1988",
                    "Hà Nam",
                    "Sài Gòn",
                    "suongnam88@gmail.com",
                    "0373741237",
                    "Đại học",
                    "Đang đi làm",
                ],
                [
                    "8",
                    "1",
                    "Maria",
                    "Lê Thắm Tiên",
                    "Nữ",
                    "22/06/2001",
                    "Đắk Lắk",
                    "",
                    "tien2001@gmail.com",
                    "0954129822",
                    "Cấp 3",
                    "Đang đi làm",
                ],
            ]

            r = self.client.post(
                "/api/v1/admin/students/import",
                json={
                    "url": "https://docs.google.com/spreadsheets/d/1CI0A9IUb5AzhJAiRzuFNsMXALTeBu0_BfqeBmKvuTJg/edit#gid=1442976576"
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            resp = r.json()
            assert r.status_code == 200

            # Check error unique numerical_order cause existed another student have numerical_order = 1
            assert len(resp["errors"]) == 1
            assert resp["errors"][0]["row"] == 2

            assert len(resp["inserted_ids"]) == 2
            mock_get_data_spreadsheet.assert_called_once()

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find({"type": AuditLogType.IMPORT, "endpoint": Endpoint.STUDENT})
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1

    def test_reset_password_student_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token, patch(
            "app.use_cases.student_admin.reset_password.generate_random_password"
        ) as mock_generate_random_password:
            mock_token.return_value = TokenData(email=self.admin.email)

            mock_password = "12345678"
            mock_generate_random_password.return_value = mock_password

            r = self.client.patch(
                f"/api/v1/admin/students/reset-password/{self.student3.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            resp = r.json()
            print(resp)
            assert r.status_code == 200
            assert resp["email"] == self.student3.email
            assert resp["password"] == mock_password

            password = StudentModel.objects(id=self.student3.id).get().password

            assert verify_password(mock_password, password)

            mock_generate_random_password.assert_called_once()

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find({"type": AuditLogType.UPDATE, "endpoint": Endpoint.STUDENT})
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1
