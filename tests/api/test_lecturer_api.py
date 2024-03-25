import app.interfaces.api_v1
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
from app.models.lecturer import LecturerModel


class TestUserApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect()
        connect("mongoenginetest", host="mongodb://localhost:1234",
                mongo_client_class=mongomock.MongoClient)
        cls.client = TestClient(app)
        cls.user: AdminModel = AdminModel(
            status="active",
            roles=[
                "bhv",
            ],
            holy_name="Martin",
            phone_number=[
                "0123456789"
            ],
            current_season=3,
            seasons=[
                3
            ],
            email="user@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.user2: AdminModel = AdminModel(
            status="active",
            roles=[
                "bkt",
            ],
            holy_name="Martin",
            phone_number=[
                "0123456789"
            ],
            current_season=3,
            seasons=[
                3
            ],
            email="user2@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.lecturer: LecturerModel = LecturerModel(
            holy_name="Phanxico",
            full_name="Nguyen Van A",
            information="string",
            contact="string"
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    def test_create_general_task(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user2.email)
            r = self.client.post(
                "/api/v1/lecturers",
                json={
                    "holy_name": "string",
                    "full_name": "string",
                    "information": "string",
                    "contact": "string"
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 403
            assert r.json().get("detail") == "Bạn không có quyền"

            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.post(
                "/api/v1/lecturers",
                json={
                    "holy_name": "Jose",
                    "full_name": "Tim",
                    "information": "string",
                    "contact": "string"
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            doc: LecturerModel = LecturerModel.objects(
                id=r.json().get("id")).get()
            assert doc.holy_name == "Jose"
            assert doc.full_name == "Tim"

    def test_get_all_lecturers(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.get(
                "/api/v1/lecturers",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["pagination"]["total"] == 2
