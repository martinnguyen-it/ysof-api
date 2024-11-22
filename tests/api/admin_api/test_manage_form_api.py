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
from app.models.lecturer import LecturerModel
from app.models.subject import SubjectModel
from app.domain.subject.enum import StatusSubjectEnum


class TestManageFormApi(unittest.TestCase):
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
            latest_season=3,
            seasons=[3],
            email="user@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.lecturer: LecturerModel = LecturerModel(
            title="Cha",
            holy_name="Phanxico",
            full_name="Nguyen Van A",
            information="Thạc sĩ thần học",
            contact="Phone: 012345657",
        ).save()
        cls.subject: SubjectModel = SubjectModel(
            title="Môn học 1",
            start_at="2024-03-27",
            subdivision="string",
            code="string",
            question_url="string",
            zoom={"meeting_id": 0, "pass_code": "string", "link": "string"},
            documents_url=["string"],
            status="init",
            lecturer=cls.lecturer,
            season=3,
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    @pytest.mark.order("first")
    def test_update_manage_form(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)

            r = self.client.post(
                "/api/v1/manage-form",
                json={"status": FormStatus.INACTIVE, "type": FormType.SUBJECT_REGISTRATION},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            resp = r.json()
            assert resp["type"] == FormType.SUBJECT_REGISTRATION
            assert resp["status"] == FormStatus.INACTIVE

            r = self.client.post(
                "/api/v1/manage-form",
                json={"status": FormStatus.ACTIVE, "type": FormType.SUBJECT_REGISTRATION},
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

    @pytest.mark.order("second")
    def test_update_manage_form_evaluation(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.post(
                "/api/v1/manage-form",
                json={"status": FormStatus.ACTIVE, "type": FormType.SUBJECT_EVALUATION},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            # cause init form evaluation or absent must have data.subject_id in payload
            assert r.status_code == 422

            r = self.client.post(
                "/api/v1/manage-form",
                json={
                    "status": FormStatus.ACTIVE,
                    "type": FormType.SUBJECT_EVALUATION,
                    "data": {"subject_id": "65f253a7fd143b81c101a63c"},
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 404  # cause not found subject

            r = self.client.post(
                "/api/v1/manage-form",
                json={
                    "status": FormStatus.ACTIVE,
                    "type": FormType.SUBJECT_EVALUATION,
                    "data": {"subject_id": str(self.subject.id)},
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["type"] == FormType.SUBJECT_EVALUATION
            assert resp["status"] == FormStatus.ACTIVE

            subject: SubjectModel = SubjectModel.objects(id=self.subject.id).get()
            assert subject.status == StatusSubjectEnum.SENT_EVALUATION

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find(
                {"type": AuditLogType.CREATE, "endpoint": Endpoint.MANAGE_FORM}
            )
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 2
            cursor = AuditLogModel._get_collection().find(
                {"type": AuditLogType.UPDATE, "endpoint": Endpoint.MANAGE_FORM}
            )
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1

    def test_get_manage_form_student_registration(self):
        r = self.client.get(
            "/api/v1/manage-form",
            params={"type": FormType.SUBJECT_REGISTRATION.value},
            headers={
                "Authorization": "Bearer {}".format("xxx"),
            },
        )

        resp = r.json()
        assert r.status_code == 200
        assert resp["status"] == FormStatus.ACTIVE
