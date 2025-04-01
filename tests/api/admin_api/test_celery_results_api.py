from datetime import datetime
import unittest
from unittest.mock import patch

from mongoengine import connect, disconnect
from pymongo.results import InsertOneResult
from fastapi.testclient import TestClient

from app.domain.auth.entity import TokenData
from app.domain.celery_result.enum import CeleryResultTag
from app.main import app

from app.models.admin import AdminModel
from app.infra.security.security_service import (
    get_password_hash,
)
from app.models.celery_result import CeleryResultModel
from app.config import settings
from app.models.season import SeasonModel


mock_data_1 = {
    "task_id": "19704e6d-a2fc-4310-befd-72f497e618e3",
    "status": "FAILURE",
    "result": {
        "tag": "send_mail",
        "name": "send_email_welcome_with_exist_account_task",
        "description": "replace() argument 2 must be str, not int",
        "traceback": 'Traceback (most recent call last):\n  File "/home/martin/src/documents/ysof/ysof-api/celery_config/celery_app_with_error_handler.py", line 23, in wrapper\n    return task_func(*args, **kwargs)\n  File "/home/martin/src/documents/ysof/ysof-api/app/infra/tasks/email.py", line 43, in send_email_welcome_with_exist_account_task\n    plain_text = plain_text.replace("{{season}}", season)\nTypeError: replace() argument 2 must be str, not int\n',
    },
    "traceback": None,
    "children": [],
    "date_done": datetime.fromisoformat("2025-03-20T09:03:26.236Z".replace("Z", "+00:00")),
}


mock_data_2 = {
    "task_id": "1950536d-a2fc-4310-befd-72f497e618e3",
    "status": "FAILURE",
    "result": {
        "tag": "default",
        "name": "send_email_welcome_with_exist_account_task",
        "description": "replace() argument 2 must be str, not int",
        "traceback": 'Traceback (most recent call last):\n  File "/home/martin/src/documents/ysof/ysof-api/celery_config/celery_app_with_error_handler.py", line 23, in wrapper\n    return task_func(*args, **kwargs)\n  File "/home/martin/src/documents/ysof/ysof-api/app/infra/tasks/email.py", line 43, in send_email_welcome_with_exist_account_task\n    plain_text = plain_text.replace("{{season}}", season)\nTypeError: replace() argument 2 must be str, not int\n',
    },
    "traceback": None,
    "children": [],
    "date_done": datetime.fromisoformat("2025-03-22T09:03:26.236Z".replace("Z", "+00:00")),
}


class TestCeleryResultsApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect()
        cls.db_name = "test_db_" + str(id(cls))
        cls.db = connect(cls.db_name, host=settings.MONGODB_HOST, port=settings.MONGODB_PORT)

        cls.client = TestClient(app)
        cls.season: SeasonModel = SeasonModel(
            title="CÙNG GIÁO HỘI, NGƯỜI TRẺ BƯỚC ĐI TRONG HY VỌNG",
            academic_year="2023-2024",
            season=2,
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
        cls.user2: AdminModel = AdminModel(
            status="active",
            roles=[
                "bkl",
            ],
            holy_name="Martin",
            phone_number=["0123456789"],
            latest_season=3,
            seasons=[3],
            email="user2@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.celery_result_1: InsertOneResult = CeleryResultModel._get_collection().insert_one(
            mock_data_1
        )
        cls.celery_result_2: InsertOneResult = CeleryResultModel._get_collection().insert_one(
            mock_data_2
        )

    @classmethod
    def tearDownClass(cls):
        # cls.db.drop_database(cls.db_name)
        disconnect()

    def test_get_list_celery_results(self):
        r = self.client.get(
            "/api/v1/celery-result",
        )
        assert r.status_code == 401

        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user2.email)
            r = self.client.get(
                "/api/v1/celery-result",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 403  # Cause only admin can get all

            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.get(
                "/api/v1/celery-result",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
                params={
                    "sort": "ascend",
                    "sort_by": "date_done",
                },
            )
            assert r.status_code == 200

            resp = r.json()
            assert resp["pagination"]["total"] == 2

            # Cause mock_data_1 date_done more early than mock_data_2
            assert resp["data"][0]["task_id"] == mock_data_1["task_id"]

    def test_get_list_celery_results_pagination(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.get(
                "/api/v1/celery-result",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
                params={"sort": "descend", "sort_by": "date_done", "page_size": 1},
            )
            assert r.status_code == 200

            resp = r.json()
            assert resp["pagination"]["total"] == 2
            assert len(resp["data"]) == 1
            assert resp["data"][0]["task_id"] == mock_data_2["task_id"]

    def test_get_list_celery_results_filter(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.get(
                "/api/v1/celery-result",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
                params={"tag": CeleryResultTag.DEFAULT.value},
            )
            assert r.status_code == 200

            resp = r.json()
            assert resp["pagination"]["total"] == 1
            assert resp["data"][0]["task_id"] == mock_data_2["task_id"]
