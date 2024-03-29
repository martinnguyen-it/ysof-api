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
from app.models.subject import SubjectModel


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
        cls.lecturer: LecturerModel = LecturerModel(
            title="Cha",
            holy_name="Phanxico",
            full_name="Nguyen Van A",
            information="Thạc sĩ thần học",
            contact="Phone: 012345657"
        ).save()
        cls.subject: SubjectModel = SubjectModel(
            title="Môn học 1",
            date="2024-03-27T14:40:51.100Z",
            subdivision="string",
            code="string",
            question_url="string",
            zoom={"meeting_id": 0, "pass_code": "string", "link": "string"},
            documents_url=[
                "string"
            ],
            lecturer=cls.lecturer,
            season=3
        ).save()
        cls.subject2: SubjectModel = SubjectModel(
            title="Môn học 2",
            date="2024-03-27T14:40:51.100Z",
            subdivision="string",
            code="string",
            question_url="string",
            zoom={"meeting_id": 0, "pass_code": "string", "link": "string"},
            documents_url=[
                "string"
            ],
            lecturer=cls.lecturer,
            season=3
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    def test_create_subject(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user2.email)

            r = self.client.post(
                "/api/v1/subjects",
                json={
                    "title": "Học hỏi",
                    "date": "2024-03-26T16:10:08.390Z",
                    "subdivision": "Kinh thánh",
                    "code": "Y10.1",
                    "question_url": "abc.com",
                    "zoom": {
                        "meeting_id": 912424124,
                        "pass_code": "123456",
                        "link": "xyz.com"
                    },
                    "documents_url": [
                        "123.com"
                    ],
                    "lecturer": str(self.lecturer.id)
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 403

            mock_token.return_value = TokenData(email=self.user1.email)

            r = self.client.post(
                "/api/v1/subjects",
                json={
                    "title": "Học hỏi",
                    "date": "2024-03-26T16:10:08.390Z",
                    "subdivision": "Kinh thánh",
                    "code": "Y10.1",
                    "question_url": "abc.com",
                    "zoom": {
                        "meeting_id": 912424124,
                        "pass_code": "123456",
                        "link": "xyz.com"
                    },
                    "documents_url": [
                        "123.com"
                    ],
                    "lecturer": str(self.lecturer.id)
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            doc: SubjectModel = SubjectModel.objects(
                id=r.json().get("id")).get()
            assert doc.title == "Học hỏi"
            assert doc.lecturer.full_name == self.lecturer.full_name

    def test_get_all_subjects(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.get(
                "/api/v1/subjects",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert len(resp) == 2

    def test_get_subject_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user2.email)
            r = self.client.get(
                f"/api/v1/subjects/{self.subject.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            doc: SubjectModel = SubjectModel.objects(
                id=r.json().get("id")).get()
            assert doc.title == self.subject.title
            assert doc.code == self.subject.code

    def test_update_subject_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user1.email)
            r = self.client.put(
                f"/api/v1/subjects/{self.subject.id}",
                json={
                    "title": "Updated"
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            doc: SubjectModel = SubjectModel.objects(
                id=r.json().get("id")).get()
            assert doc.title == "Updated"

    def test_delete_subject_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user2.email)
            r = self.client.delete(
                f"/api/v1/subjects/{self.subject2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 403

            mock_token.return_value = TokenData(email=self.user1.email)
            r = self.client.delete(
                f"/api/v1/subjects/{self.subject2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200

            r = self.client.get(
                f"/api/v1/subjects/{self.subject2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 404
