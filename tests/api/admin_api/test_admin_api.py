import time
import unittest
from unittest.mock import patch
from google.oauth2.credentials import Credentials
from mongoengine import connect, disconnect
from fastapi.testclient import TestClient
from app.config import settings
from app.domain.upload.entity import GoogleDriveAPIRes
from app.main import app
import mongomock

from app.models.admin import AdminModel
from app.infra.security.security_service import (
    TokenData,
    get_password_hash,
)
from app.models.season import SeasonModel
from app.models.audit_log import AuditLogModel
from app.domain.audit_log.enum import AuditLogType, Endpoint


class TestAdminApi(unittest.TestCase):
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
        cls.user: AdminModel = AdminModel(
            status="active",
            roles=[
                "admin",
            ],
            holy_name="Martin",
            phone_number=["0123456789"],
            latest_season=2,
            seasons=[2],
            email="user@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.user1: AdminModel = AdminModel(
            status="active",
            roles=[
                "bdh",
            ],
            holy_name="Martin",
            phone_number=["0123456789"],
            latest_season=3,
            seasons=[1, 2, 3],
            email="user1@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.user2: AdminModel = AdminModel(
            status="active",
            roles=[
                "bdh",
            ],
            holy_name="Martin",
            phone_number=["0123456789"],
            latest_season=2,
            seasons=[2],
            email="user2@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.user3: AdminModel = AdminModel(
            status="active",
            roles=[
                "bhv",
            ],
            holy_name="Martin",
            phone_number=["0123456789"],
            latest_season=3,
            seasons=[3],
            email="user3@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    def test_create_admin(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token, patch(
            "app.infra.tasks.email.send_email_welcome_task.delay"
        ), patch("app.infra.tasks.email.send_email_welcome_with_exist_account_task.delay"):
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.post(
                "/api/v1/admins",
                json={
                    "email": "test@test.com",
                    "roles": ["admin"],
                    "full_name": "string",
                    "holy_name": "string",
                    "phone_number": ["string"],
                    "address": {"current": "string", "original": "string", "diocese": "string"},
                    "date_of_birth": "2024-03-15",
                    "facebook": "string",
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            user: AdminModel = AdminModel.objects(id=r.json().get("id")).get()
            assert user.email == "test@test.com"
            assert user.created_at
            assert user.updated_at
            assert user.password

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find(
                {"type": AuditLogType.CREATE, "endpoint": Endpoint.ADMIN}
            )
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1

    def test_get_myself(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.get(
                "/api/v1/admins/me",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp.get("email") == "user@example.com"

    def test_get_admin(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.get(
                f"/api/v1/admins/{str(self.user.id)}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp.get("email") == "user@example.com"

    def test_update_admin(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            # test forbidden
            mock_token.return_value = TokenData(email=self.user2.email)
            r = self.client.put(
                f"/api/v1/admins/{str(self.user3.id)}",
                json={"full_name": "Updated"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 403

            # test success
            mock_token.return_value = TokenData(email=self.user1.email)
            r = self.client.put(
                f"/api/v1/admins/{str(self.user3.id)}",
                json={"full_name": "Updated"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp.get("full_name") == "Updated"

            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.put(
                f"/api/v1/admins/{str(self.user3.id)}",
                json={"full_name": "Updated"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find(
                {"type": AuditLogType.UPDATE, "endpoint": Endpoint.ADMIN}
            )
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 2

    def test_update_avatar_me(self):
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
                "/api/v1/admins/me/avatar",
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
                "/api/v1/admins/me/avatar",
                files=file3,
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 400
            assert r.json()["detail"] == "image: Ảnh đại diện phải là hình vuông."

            r = self.client.put(
                "/api/v1/admins/me/avatar",
                files=file4,
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            resp = r.json()
            assert resp["avatar"] == "https://lh3.googleusercontent.com/d/{}".format(mock_id)
            assert resp["email"] == self.user.email
            mock_upload_to_drive.assert_called_once()
            user: AdminModel = AdminModel.objects(id=self.user.id).get()
            assert user.avatar == f"{settings.PREFIX_IMAGE_GCLOUD}{mock_id}"
