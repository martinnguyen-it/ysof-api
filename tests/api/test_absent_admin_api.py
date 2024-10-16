import time
import unittest
import pytest
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
from app.models.lecturer import LecturerModel
from app.models.subject import SubjectModel
from app.models.season import SeasonModel
from app.models.student import StudentModel
from app.models.absent import AbsentModel
from app.models.audit_log import AuditLogModel
from app.domain.audit_log.enum import AuditLogType, Endpoint


class TestAdminAbsentApi(unittest.TestCase):
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
                "bkl",
            ],
            holy_name="Martin",
            phone_number=["0123456789"],
            latest_season=3,
            seasons=[3],
            email="user1@example.com",
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
        cls.student: StudentModel = StudentModel(
            numerical_order=1,
            group=2,
            status="active",
            holy_name="Martin",
            phone_number="0123456789",
            latest_season=3,
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
            latest_season=3,
            email="student2@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.absent: AbsentModel = AbsentModel(
            subject=cls.subject, student=cls.student2, reason="Xin phép nghỉ", status=True
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    @pytest.mark.order(1)
    def test_create_absent(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.admin.email)
            r = self.client.post(
                f"/api/v1/absents/subject/{self.subject.id}/student/{self.student2.id}",
                json={"reason": "Xin phép nghỉ"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 400
            assert r.json()["detail"] == "Đơn nghỉ phép đã được tạo trước đây."

            r = self.client.post(
                f"/api/v1/absents/subject/{self.subject.id}/student/{self.student.id}",
                json={"reason": "Xin phép nghỉ"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            resp = r.json()
            assert r.status_code == 200
            assert resp["reason"] == "Xin phép nghỉ"
            assert resp["subject"]
            assert resp["student"]

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find({"type": AuditLogType.CREATE, "endpoint": Endpoint.ABSENT})
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1

    @pytest.mark.order(2)
    def test_update_absent(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.admin.email)
            r = self.client.patch(
                f"/api/v1/absents/subject/{self.subject.id}/student/{self.student.id}",
                json={
                    "reason": "Updated",
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["reason"] == "Updated"

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find({"type": AuditLogType.UPDATE, "endpoint": Endpoint.ABSENT})
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1

    @pytest.mark.order(3)
    def test_get_absent_by_subject_id_and_student_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.admin.email)
            r = self.client.get(
                f"/api/v1/absents/subject/{self.subject.id}/student/{self.student.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["reason"] == "Updated"

    @pytest.mark.order(4)
    def test_get_list_absent_by_subject_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.admin.email)
            r = self.client.get(
                f"/api/v1/absents/{self.subject.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert len(resp) == 2

    @pytest.mark.order(5)
    def test_delete_absent_by_subject_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.admin.email)
            r = self.client.delete(
                f"/api/v1/absents/subject/{self.subject.id}/student/{self.student.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200

            r = self.client.get(
                f"/api/v1/absents/subject/{self.subject.id}/student/{self.student.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 404

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find({"type": AuditLogType.DELETE, "endpoint": Endpoint.ABSENT})
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1
