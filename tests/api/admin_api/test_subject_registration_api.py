import pytest
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
from app.models.student import SeasonInfo, StudentModel
from app.models.subject import SubjectModel
from app.models.lecturer import LecturerModel
from app.models.subject_registration import SubjectRegistrationModel


class TestSubjectRegistrationApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect()
        connect(
            "mongoenginetest",
            host="mongodb://localhost:1234",
            mongo_client_class=mongomock.MongoClient,
        )
        cls.client = TestClient(app)
        cls.season: SeasonModel = SeasonModel(
            title="CÙNG GIÁO HỘI, NGƯỜI TRẺ BƯỚC ĐI TRONG HY VỌNG",
            academic_year="2023-2024",
            season=3,
            is_current=True,
        ).save()
        cls.admin: AdminModel = AdminModel(
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
        cls.lecturer: LecturerModel = LecturerModel(
            title="Cha",
            holy_name="Phanxico",
            full_name="Nguyen Van A",
            information="Thạc sĩ thần học",
            contact="Phone: 012345657",
        ).save()
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
        cls.student2: StudentModel = StudentModel(
            seasons_info=[
                SeasonInfo(
                    numerical_order=2,
                    group=2,
                    season=3,
                )
            ],
            status="active",
            holy_name="Martin",
            phone_number="0123456789",
            email="student2@example.com",
            full_name="Hoang Van B",
            password=get_password_hash(password="local@local"),
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
        cls.subject2: SubjectModel = SubjectModel(
            title="Môn học 2",
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

        cls.registration: SubjectRegistrationModel = SubjectRegistrationModel(
            student=cls.student.id,
            subject=cls.subject.id,
        ).save()
        cls.registration2: SubjectRegistrationModel = SubjectRegistrationModel(
            student=cls.student2.id, subject=cls.subject.id
        )

    @classmethod
    def tearDownClass(cls):
        disconnect()

    @pytest.mark.order(1)
    def test_get_list_registration(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.admin.email)

            r = self.client.get(
                "/api/v1/subjects/registration",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["pagination"]["total"] == 2
            assert len(resp["data"]) == 2
            registration = resp["data"][0]
            assert registration["student"]["id"] == str(self.student.id)
            assert registration["total"] == 1
            assert registration["subject_registrations"][0] == str(self.subject.id)

    @pytest.mark.order(2)
    def test_get_list_student_registration_by_subject_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.admin.email)

            r = self.client.get(
                "/api/v1/subjects/registration/subject/{}".format(self.subject.id),
                params={"search": self.student.full_name},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert len(resp) == 1
            registration = resp[0]
            assert registration["id"] == str(self.student.id)

    @pytest.mark.order(3)
    def test_admin_register_student_for_subjects(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.admin.email)

            # Test admin registering a student for subjects
            r = self.client.post(
                "/api/v1/subjects/registration",
                json={
                    "student_id": str(self.student2.id),
                    "subjects": [str(self.subject.id), str(self.subject2.id)],
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["student_id"] == str(self.student2.id)
            assert len(resp["subjects_registration"]) == 2
            assert str(self.subject.id) in resp["subjects_registration"]
            assert str(self.subject2.id) in resp["subjects_registration"]

    @pytest.mark.order(4)
    def test_admin_register_nonexistent_student(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.admin.email)

            # Test admin trying to register a non-existent student
            r = self.client.post(
                "/api/v1/subjects/registration",
                json={
                    "student_id": "507f1f77bcf86cd799439011",  # Non-existent student ID
                    "subjects": [str(self.subject.id)],
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 404
            assert "Học viên không tồn tại" in r.json()["detail"]
