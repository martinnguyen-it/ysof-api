import unittest
from unittest.mock import patch
from mongoengine import connect, disconnect
from fastapi.testclient import TestClient
from app.config import settings
from app.domain.upload.entity import GoogleDriveAPIRes
from app.main import app
import mongomock
from google.oauth2.credentials import Credentials

from app.models.student import SeasonInfo, StudentModel
from app.infra.security.security_service import get_password_hash, TokenData
from app.models.season import SeasonModel


class TestStudentApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect()
        connect(
            "mongoenginetest",
            host="mongodb://localhost:1234",
            mongo_client_class=mongomock.MongoClient,
        )
        cls.client = TestClient(app)
        cls.season: SeasonModel = SeasonModel(
            title="CÙNG GIÁO HỘI, NGƯỜI TRẺ BƯỚC ĐI TRONG HY VỌNG",
            academic_year="2023-2024",
            season=3,
            is_current=True,
        ).save()
        cls.student: StudentModel = StudentModel(
            seasons_info=[
                SeasonInfo(
                    numerical_order=1,
                    group=2,
                    season=3,
                )
            ],
            status="active",
            holy_name="Martin",
            phone_number="0123456789",
            email="student@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.student2: StudentModel = StudentModel(
            seasons_info=[
                SeasonInfo(
                    numerical_order=2,
                    group=2,
                    season=3,
                )
            ],
            status="active",
            holy_name="Martin",
            phone_number="0123456789",
            email="student2@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    def test_student_get_me(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student.email)
            r = self.client.get(
                "/api/v1/student/students/me",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            resp = r.json()
            assert "password" not in resp
            assert resp["email"] == self.student.email
            assert resp["full_name"] == self.student.full_name
            assert resp["phone_number"] == self.student.phone_number

    def test_student_get_list(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student.email)
            r = self.client.get(
                "/api/v1/student/students",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            resp = r.json()
            assert resp["pagination"]["total"] == 2
            assert "password" not in resp["data"][0]
            assert "*" in resp["data"][0]["email"]
            assert "*" in resp["data"][0]["phone_number"]

    def test_update_admin(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student.email)
            r = self.client.put(
                "/api/v1/student/students/me",
                json={"full_name": "Updated"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200

    def test_update_avatar_me(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token, patch(
            "app.infra.services.google_drive_api.GoogleDriveAPIService.create"
        ) as mock_upload_to_drive, patch(
            "app.infra.services.google_drive_api.GoogleDriveAPIService._get_oauth_token"
        ) as mock_get_oauth_token:
            mock_token.return_value = TokenData(email=self.student.email)
            mock_get_oauth_token.return_value = Credentials(
                token="<access_token>",
                refresh_token="<refresh_token>",
                client_id="<client_id>",
                client_secret="<client_secret>",
                token_uri="<token_uri>",
                scopes=["https://www.googleapis.com/auth/drive"],
            )

            mock_id = "1_YHlcIIE7b6tftTgknPB_freQRJfiOmy"
            mock_upload_to_drive.return_value = GoogleDriveAPIRes.model_validate(
                {
                    "id": mock_id,
                    "mimeType": "application/pdf",
                    "name": "test.pdf",
                }
            )

            file1 = {"image": open("tests/mocks/sample.pdf", "rb")}
            file3 = {"image": open("tests/mocks/avatar-not-square.png", "rb")}
            file4 = {"image": open("tests/mocks/avatar-square.png", "rb")}

            r = self.client.put(
                "/api/v1/student/students/me/avatar",
                files=file1,
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            # Fail cause file isn't image
            assert r.status_code == 400
            assert (
                r.json()["detail"]
                == "image: Ảnh phải nhỏ hơn 200KB\nimage: Không đúng định dạng ảnh."
            )

            r = self.client.put(
                "/api/v1/student/students/me/avatar",
                files=file3,
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 400
            assert r.json()["detail"] == "image: Ảnh đại diện phải là hình vuông."

            r = self.client.put(
                "/api/v1/student/students/me/avatar",
                files=file4,
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            mock_upload_to_drive.assert_called_once()
            student: StudentModel = StudentModel.objects(id=self.student.id).get()
            assert student.avatar == f"{settings.PREFIX_IMAGE_GCLOUD}{mock_id}"
