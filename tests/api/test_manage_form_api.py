import time
import unittest
from unittest.mock import patch
import pytest

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
from app.domain.manage_form.enum import FormStatus, FormType


class TestUserApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect()
        connect("mongoenginetest", host="mongodb://localhost:1234", mongo_client_class=mongomock.MongoClient)
        cls.client = TestClient(app)
        cls.season: SeasonModel = SeasonModel(
            title="CÙNG GIÁO HỘI, NGƯỜI TRẺ BƯỚC ĐI TRONG HY VỌNG", academic_year="2023-2024", season=3, is_current=True
        ).save()
        cls.user: AdminModel = AdminModel(
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

    @pytest.mark.order(1)
    def test_update_manage_form_student_registration(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)

            r = self.client.post(
                "/api/v1/manage-form/subject-registration",
                json={"status": "inactive"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            resp = r.json()
            assert resp["type"] == FormType.SUBJECT_REGISTRATION
            assert resp["status"] == FormStatus.INACTIVE

            r = self.client.post(
                "/api/v1/manage-form/subject-registration",
                json={"status": "active"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            resp = r.json()
            assert resp["type"] == FormType.SUBJECT_REGISTRATION
            assert resp["status"] == FormStatus.ACTIVE

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find(
                {"type": AuditLogType.CREATE, "endpoint": Endpoint.MANAGE_FORM}
            )
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1
            cursor = AuditLogModel._get_collection().find(
                {"type": AuditLogType.UPDATE, "endpoint": Endpoint.MANAGE_FORM}
            )
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1

    @pytest.mark.order(2)
    def test_get_manage_form_student_registration(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)

            r = self.client.get(
                "/api/v1/manage-form/subject-registration",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            resp = r.json()
            assert resp["type"] == FormType.SUBJECT_REGISTRATION
            assert resp["status"] == FormStatus.ACTIVE
