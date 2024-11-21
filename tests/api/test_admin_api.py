import time
import unittest
from unittest.mock import patch
from mongoengine import connect, disconnect
from fastapi.testclient import TestClient
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
        cls.user = AdminModel(
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
        cls.user1 = AdminModel(
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
        cls.user2 = AdminModel(
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
        cls.user3 = AdminModel(
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
