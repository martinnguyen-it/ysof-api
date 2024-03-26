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
                "admin",
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
        cls.user1: AdminModel = AdminModel(
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
            email="user1@example.com",
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
            title="Cha",
            holy_name="Phanxico",
            full_name="Nguyen Van A",
            information="string",
            contact="string"
        ).save()
        cls.lecturer2: LecturerModel = LecturerModel(
            title="Nhóm",
            holy_name="Phanxico",
            full_name="Nguyen Van A",
            information="string",
            contact="string"
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    def test_create_lecturer(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user2.email)
            r = self.client.post(
                "/api/v1/lecturers",
                json={
                    "title": "Sơ",
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

            mock_token.return_value = TokenData(email=self.user1.email)
            r = self.client.post(
                "/api/v1/lecturers",
                json={
                    "title": "Cha",
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
            assert doc.title == "Cha"
            assert doc.holy_name == "Jose"
            assert doc.full_name == "Tim"

    def test_get_all_lecturers(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user2.email)
            r = self.client.get(
                "/api/v1/lecturers",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["pagination"]["total"] == 2

    def test_get_lecturer_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user2.email)
            r = self.client.get(
                f"/api/v1/lecturers/{self.lecturer.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            doc: LecturerModel = LecturerModel.objects(
                id=r.json().get("id")).get()
            assert doc.holy_name == self.lecturer.holy_name
            assert doc.full_name == self.lecturer.full_name

    def test_update_lecturer_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user1.email)
            r = self.client.put(
                f"/api/v1/lecturers/{self.lecturer.id}",
                json={
                    "full_name": "Updated"
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            doc: LecturerModel = LecturerModel.objects(
                id=r.json().get("id")).get()
            assert doc.full_name == "Updated"

    def test_delete_lecturer_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user1.email)
            r = self.client.delete(
                f"/api/v1/lecturers/{self.lecturer2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 403

            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.delete(
                f"/api/v1/lecturers/{self.lecturer2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200

            r = self.client.get(
                f"/api/v1/lecturers/{self.lecturer2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 404
