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
from app.models.season import SeasonModel


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
        cls.user2: AdminModel = AdminModel(
            status="active",
            roles=[
                "bkl",
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
        cls.season: SeasonModel = SeasonModel(
            title="CÙNG GIÁO HỘI, NGƯỜI TRẺ BƯỚC ĐI TRONG HY VỌNG",
            academic_year="2023-2024",
            season=2,
            is_current=False
        ).save()
        cls.season2: SeasonModel = SeasonModel(
            title="Truong hoc",
            academic_year="2022-2023",
            season=1,
            is_current=True
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    def test_create_season(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user2.email)
            r = self.client.post(
                "/api/v1/seasons",
                json={
                    "title": "CÙNG GIÊSU, NGƯỜI TRẺ DÁM ƯỚC MƠ",
                    "season": 3,
                    "academic_year": "2023-2024"
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 403

            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.post(
                "/api/v1/seasons",
                json={
                    "title": "CÙNG GIÊSU, NGƯỜI TRẺ DÁM ƯỚC MƠ",
                    "season": 3,
                    "academic_year": "2023-2024"
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            doc: SeasonModel = SeasonModel.objects(
                id=r.json().get("id")).get()
            assert doc.title == "CÙNG GIÊSU, NGƯỜI TRẺ DÁM ƯỚC MƠ"
            assert doc.season == 3

    def test_get_all_seasons(self):
        r = self.client.get(
            "/api/v1/seasons",
        )
        assert r.status_code == 200
        resp = r.json()
        assert len(resp) == 2

    def test_get_season_by_id(self):
        r = self.client.get(
            f"/api/v1/seasons/{self.season.id}",
        )
        assert r.status_code == 200
        doc: SeasonModel = SeasonModel.objects(
            id=r.json().get("id")).get()
        assert doc.title == self.season.title

    def test_get_current_season(self):
        r = self.client.get(
            "/api/v1/seasons/current",
        )
        assert r.status_code == 200
        doc: SeasonModel = SeasonModel.objects(
            id=r.json().get("id")).get()
        assert doc.is_current is True

    def test_update_season_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.put(
                f"/api/v1/seasons/{self.season.id}",
                json={
                    "title": "Updated"
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            doc: SeasonModel = SeasonModel.objects(
                id=r.json().get("id")).get()
            assert doc.title == "Updated"

    def test_mark_current_season_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.put(
                f"/api/v1/seasons/{self.season.id}/current",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            doc: SeasonModel = SeasonModel.objects(
                id=r.json().get("id")).get()
            assert doc.is_current is True

    def test_delete_season_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user2.email)
            r = self.client.delete(
                f"/api/v1/seasons/{self.season2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 403

            mock_token.return_value = TokenData(email=self.user.email)
            # Test can't delete season is current season  (is_current == True)
            doc: SeasonModel = SeasonModel.objects(is_current=True).get()
            r = self.client.delete(
                f"/api/v1/seasons/{doc.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 400
            assert "Không thể xóa" in r.json().get("detail")

            r = self.client.delete(
                f"/api/v1/seasons/{self.season2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200

            r = self.client.get(
                f"/api/v1/seasons/{self.season2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 404
