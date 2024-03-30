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
from app.models.document import DocumentModel
from app.models.general_task import GeneralTaskModel
from app.models.season import SeasonModel


class TestUserApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect()
        connect("mongoenginetest", host="mongodb://localhost:1234",
                mongo_client_class=mongomock.MongoClient)
        cls.client = TestClient(app)
        cls.season: SeasonModel = SeasonModel(
            title="CÙNG GIÁO HỘI, NGƯỜI TRẺ BƯỚC ĐI TRONG HY VỌNG",
            academic_year="2023-2024",
            season=3,
            is_current=True
        ).save()
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
        cls.document: DocumentModel = DocumentModel(
            file_id="1hXt8WI3g6p8YUtN2gR35yA-gO_fE2vD3",
            mimeType="image/jpeg",
            name="Tài liệu học",
            thumbnailLink="https://lh3.googleusercontent.com/drive-storage/AJQWtBPQ0cDHLtK8eFG3nyGUQ02897KWOM87NIeoCu6OSyOoehPiZrY7__MpTVFAxsSM3UBsJz-4yDVoB-yio8LMQsaqQpNsgewuzf3F2VCI=s220",
            role="bhv",
            type="common",
            label=[
                "string"
            ],
            season=3,
            author=cls.user
        ).save()
        cls.general_task: GeneralTaskModel = GeneralTaskModel(
            title="Cong viec dau nam",
            short_desc="Cong viec",
            description="Đoạn văn là một đơn vị văn bản nhỏ",
            start_at="2024-03-22T08:26:54.965000Z",
            end_at="2024-03-22T08:26:54.965000Z",
            role="bhv",
            type="common",
            label=[
                "string"
            ],
            season=3,
            author=cls.user,
            attachments=[cls.document]
        ).save()
        cls.general_task2: GeneralTaskModel = GeneralTaskModel(
            title="Cong viec dau nam",
            short_desc="Cong viec",
            description="Đoạn văn là một đơn vị văn bản nhỏ",
            start_at="2024-03-22T08:26:54.965000Z",
            end_at="2024-03-22T08:26:54.965000Z",
            role="bhv",
            type="common",
            label=[
                "string"
            ],
            season=3,
            author=cls.user,
            attachments=[cls.document]
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    def test_create_general_task(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.post(
                "/api/v1/general-tasks",
                json={
                    "title": "Tai lieu",
                    "short_desc": "string",
                    "description": "string",
                    "start_at": "2024-03-22T09:37:15.278Z",
                    "end_at": "2024-03-22T09:37:15.278Z",
                    "role": "string",
                    "label": [
                            "string"
                    ],
                    "type": "annual",
                    "attachments": ["65f867130d52617a8b07002b"]
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 404
            assert r.json().get("detail") == "Tài liệu đính kèm không tồn tại"

            r = self.client.post(
                "/api/v1/general-tasks",
                json={
                    "title": "Tai lieu",
                    "short_desc": "string",
                    "description": "string",
                    "start_at": "2024-03-22T09:37:15.278Z",
                    "end_at": "2024-03-22T09:37:15.278Z",
                    "role": "bhv",
                    "label": [
                            "string"
                    ],
                    "type": "annual",
                    "attachments": [str(self.document.id)]
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            doc: GeneralTaskModel = GeneralTaskModel.objects(
                id=r.json().get("id")).get()
            assert doc.title == "Tai lieu"
            assert doc.role == "bhv"
            assert len(doc.attachments) == 1

    def test_get_general_task_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.get(
                f"/api/v1/general-tasks/{self.general_task.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            doc: GeneralTaskModel = GeneralTaskModel.objects(
                id=r.json().get("id")).get()
            assert doc.title == self.general_task.title
            assert doc.role
            assert doc.description

    def test_get_all_general_tasks(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.get(
                "/api/v1/general-tasks",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["pagination"]["total"] == 2

    def test_update_general_task_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.put(
                f"/api/v1/general-tasks/{self.general_task.id}",
                json={
                    "title": "Updated"
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            doc: GeneralTaskModel = GeneralTaskModel.objects(
                id=r.json().get("id")).get()
            assert doc.title == "Updated"

    def test_delete_general_task_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.delete(
                f"/api/v1/general-tasks/{self.general_task2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200

            r = self.client.get(
                f"/api/v1/general-tasks/{self.general_task2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 404
