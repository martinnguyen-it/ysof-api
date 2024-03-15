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


class TestUserApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect()
        connect("mongoenginetest", host="mongodb://localhost:1234",
                mongo_client_class=mongomock.MongoClient)
        cls.client = TestClient(app)
        cls.user = AdminModel(
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

    @classmethod
    def tearDownClass(cls):
        disconnect()

    def test_create_user(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.post(
                "/api/v1/admins",
                json={
                    "email": "test@test.com",
                    "roles": [
                        "admin"
                    ],
                    "full_name": "string",
                    "holy_name": "string",
                    "phone_number": [
                        "string"
                    ],
                    "address": {
                        "current": "string",
                        "original": "string",
                        "diocese": "string"
                    },
                    "date_of_birth": "2024-03-15T17:10:57.939Z",
                    "facebook": "string"
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            user = AdminModel.objects(id=r.json().get("id")).get()
            assert user.email == "test@test.com"
            assert user.created_at
            assert user.updated_at
            assert user.password

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

    def test_get_user(self):
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
