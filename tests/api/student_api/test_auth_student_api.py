import unittest
from mongoengine import connect, disconnect
from fastapi.testclient import TestClient
from app.main import app
import mongomock
from app.infra.security.security_service import get_password_hash, verify_password
from app.models.student import SeasonInfo, StudentModel
import pytest
from unittest.mock import patch
from app.domain.auth.entity import TokenData


class TestAuthAdminStudentApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect()
        connect(
            "mongoenginetest",
            host="mongodb://localhost:1234",
            mongo_client_class=mongomock.MongoClient,
        )
        cls.client = TestClient(app)
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

    @classmethod
    def tearDownClass(cls):
        disconnect()

    @pytest.mark.order(1)
    def test_admin_login(self):
        r = self.client.post(
            "/api/v1/student/auth/login",
            json={"email": "student@example.com", "password": "local@local"},
        )
        assert r.status_code == 200
        assert r.json().get("access_token")

    @pytest.mark.order(2)
    def test_admin_change_password(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student.email)
            new_password = "new_password"

            r = self.client.put(
                "/api/v1/student/auth/change-password",
                json={"new_password": new_password, "old_password": "dummy"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 400
            assert r.json().get("detail") == "Sai mật khẩu"

            r = self.client.put(
                "/api/v1/student/auth/change-password",
                json={"new_password": new_password, "old_password": "local@local"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            student: StudentModel = StudentModel.objects(id=self.student.id).get()
            assert verify_password(new_password, student.password)
