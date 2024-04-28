import unittest
import pytest
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
from app.models.season import SeasonModel
from app.models.student import StudentModel
from app.models.absent import AbsentModel
from app.models.manage_form import ManageFormModel
from app.domain.manage_form.enum import FormStatus, FormType


class TestAbsentApi(unittest.TestCase):
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
                "bhv",
            ],
            holy_name="Martin",
            phone_number=["0123456789"],
            current_season=3,
            seasons=[3],
            email="user1@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.lecturer: LecturerModel = LecturerModel(
            title="Cha",
            holy_name="Phanxico",
            full_name="Nguyen Van A",
            information="Thạc sĩ thần học",
            contact="Phone: 012345657",
        ).save()
        cls.subject: SubjectModel = SubjectModel(
            title="Môn học 1",
            start_at="2024-03-27",
            subdivision="string",
            code="string",
            question_url="string",
            zoom={"meeting_id": 0, "pass_code": "string", "link": "string"},
            documents_url=["string"],
            lecturer=cls.lecturer,
            status="init",
            season=3,
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
        cls.absent: AbsentModel = AbsentModel(
            subject=cls.subject, student=cls.student2, reason="Xin phép nghỉ", status=True
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    @pytest.mark.order(1)
    def test_create_absent(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student.email)
            r = self.client.post(
                f"/api/v1/student/absent/{self.subject.id}",
                json={"reason": "Xin phép nghỉ"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 400
            assert r.json()["detail"].startswith("Form chưa được mở")

            # Open form with dummy subject id
            manage_form = ManageFormModel(
                type=FormType.SUBJECT_ABSENT,
                status=FormStatus.ACTIVE,
                data={"subject_id": "65f253a7fd143b81c101a63c"},
            ).save()
            r = self.client.post(
                f"/api/v1/student/absent/{self.subject.id}",
                json={"reason": "Xin phép nghỉ"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 400
            assert r.json()["detail"] == "Form hiện tại không mở cho môn học này."

            ManageFormModel.objects(id=manage_form.id).update_one(
                data={"subject_id": str(self.subject.id)},
                upsert=False,
            )
            manage_form.reload()

            r = self.client.post(
                f"/api/v1/student/absent/{self.subject.id}",
                json={"reason": "Xin phép nghỉ"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            resp = r.json()
            assert r.status_code == 200
            assert resp["reason"] == "Xin phép nghỉ"
            assert resp["subject"]
            assert "student" not in resp

    @pytest.mark.order(2)
    def test_update_absent(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student2.email)
            r = self.client.patch(
                f"/api/v1/student/absent/{self.subject.id}",
                json={
                    "reason": "Updated",
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["reason"] == "Updated"

    @pytest.mark.order(3)
    def test_get_absent_by_subject_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student2.email)
            r = self.client.get(
                f"/api/v1/student/absent/{self.subject.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["reason"] == "Updated"

    @pytest.mark.order(4)
    def test_delete_absent_by_subject_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student2.email)
            r = self.client.delete(
                f"/api/v1/student/absent/{self.subject.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200

            r = self.client.get(
                f"/api/v1/student/absent/{self.subject.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 404
