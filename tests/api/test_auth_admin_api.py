import unittest
from mongoengine import connect, disconnect
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
import mongomock
from app.infra.security.security_service import get_password_hash, TokenData
from app.models.admin import AdminModel


class TestAuthAdminApi(unittest.TestCase):
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

    def test_admin_login(self):
        r = self.client.post(
            "/api/v1/admin/auth/login", json={"email": "user@example.com", "password": "local@local"})
        assert r.status_code == 200
        assert r.json().get("access_token")
