import app.interfaces.api_v1
import time
import unittest
from unittest.mock import patch
from mongoengine import connect, disconnect
from fastapi.testclient import TestClient
from app.main import app
import mongomock

from app.models.student import StudentModel
from app.models.admin import AdminModel
from app.infra.security.security_service import (
    TokenData,
    get_password_hash,
)
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
                    "date_of_birth": "2024-04-06T10:18:39.070Z",
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
                    "date_of_birth": "2024-04-06T10:18:39.070Z",
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
            assert resp["pagination"]["total"] == 2

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
            assert len(audit_logs) == 1

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
