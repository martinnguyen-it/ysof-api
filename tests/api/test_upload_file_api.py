import unittest
from unittest.mock import patch

from google.oauth2.credentials import Credentials
from mongoengine import connect, disconnect
from fastapi.testclient import TestClient

from app.domain.upload.entity import GoogleDriveAPIRes
from app.main import app
import mongomock

from app.models.admin import AdminModel
from app.infra.security.security_service import (
    TokenData,
    get_password_hash,
)
from app.models.season import SeasonModel


class TestUploadFileApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect()
        connect("mongoenginetest", host="mongodb://localhost:1234", mongo_client_class=mongomock.MongoClient)
        cls.client = TestClient(app)
        cls.season: SeasonModel = SeasonModel(
            title="CÙNG GIÁO HỘI, NGƯỜI TRẺ BƯỚC ĐI TRONG HY VỌNG", academic_year="2023-2024", season=3, is_current=True
        ).save()
        cls.user = AdminModel(
            status="active",
            roles=[
                "admin",
            ],
            holy_name="Martin",
            phone_number=["0123456789"],
            current_season=3,
            seasons=[3],
            email="user@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    def test_upload_file(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token, patch(
            "app.infra.services.google_drive_api.GoogleDriveAPIService.create"
        ) as mock_upload_to_drive, patch(
            "app.infra.services.google_drive_api.GoogleDriveAPIService._get_oauth_token"
        ) as mock_get_oauth_token:
            mock_token.return_value = TokenData(email=self.user.email)
            mock_get_oauth_token.return_value = Credentials(
                token="<access_token>",
                refresh_token="<refresh_token>",
                client_id="<client_id>",
                client_secret="<client_secret>",
                token_uri="<token_uri>",
                scopes=["https://www.googleapis.com/auth/drive"],
            )
            mock_upload_to_drive.return_value = GoogleDriveAPIRes.model_validate(
                {
                    "id": "1_YHlcIIE7b6tftTgknPB_freQRJfiOmy",
                    "mimeType": "application/pdf",
                    "name": "test.pdf",
                }
            )

            files = {"file": open("tests/mocks/sample.pdf", "rb")}

            r = self.client.post(
                "/api/v1/upload",
                files=files,
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            mock_upload_to_drive.assert_called_once()

    def test_upload_image(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token, patch(
            "app.infra.services.google_drive_api.GoogleDriveAPIService.create"
        ) as mock_upload_to_drive, patch(
            "app.infra.services.google_drive_api.GoogleDriveAPIService._get_oauth_token"
        ) as mock_get_oauth_token:
            mock_token.return_value = TokenData(email=self.user.email)
            mock_get_oauth_token.return_value = Credentials(
                token="<access_token>",
                refresh_token="<refresh_token>",
                client_id="<client_id>",
                client_secret="<client_secret>",
                token_uri="<token_uri>",
                scopes=["https://www.googleapis.com/auth/drive"],
            )
            mock_upload_to_drive.return_value = GoogleDriveAPIRes.model_validate(
                {
                    "id": "1_YHlcIIE7b6tftTgknPB_freQRJfiOmy",
                    "mimeType": "application/pdf",
                    "name": "test.pdf",
                }
            )

            file1 = {"image": open("tests/mocks/sample.pdf", "rb")}
            file2 = {"image": open("tests/mocks/ysof.jpg", "rb")}

            r = self.client.post(
                "/api/v1/upload/image",
                files=file1,
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            # Fail cause file isn't image
            assert r.status_code == 400

            r = self.client.post(
                "/api/v1/upload/image",
                files=file2,
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            mock_upload_to_drive.assert_called_once()

    def test_delete_file(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token, patch(
            "app.infra.services.google_drive_api.GoogleDriveAPIService.delete"
        ), patch("app.infra.services.google_drive_api.GoogleDriveAPIService._get_oauth_token") as mock_get_oauth_token:
            mock_token.return_value = TokenData(email=self.user.email)
            mock_get_oauth_token.return_value = Credentials(
                token="<access_token>",
                refresh_token="<refresh_token>",
                client_id="<client_id>",
                client_secret="<client_secret>",
                token_uri="<token_uri>",
                scopes=["https://www.googleapis.com/auth/drive"],
            )

            r = self.client.delete(
                "/api/v1/upload/abc",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
