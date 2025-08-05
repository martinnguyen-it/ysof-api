import pytest
import unittest
import time
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
from app.models.audit_log import AuditLogModel
from app.domain.audit_log.enum import AuditLogType, Endpoint


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

            # Verify summary field exists and contains correct data
            assert "summary" in resp
            assert isinstance(resp["summary"], dict)
            # Should have 1 student registered for subject.id
            assert str(self.subject.id) in resp["summary"]
            assert resp["summary"][str(self.subject.id)] == 1

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

            # Verify audit log was created
            time.sleep(1)
            cursor = AuditLogModel._get_collection().find(
                {"type": AuditLogType.UPDATE, "endpoint": Endpoint.STUDENT}
            )
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1

            # Verify audit log details
            audit_log = audit_logs[0]
            assert audit_log.author_name == self.admin.full_name
            assert audit_log.author_email == self.admin.email
            assert audit_log.author_roles == self.admin.roles
            assert audit_log.season == 3

            # Parse description to verify content
            import json

            description = json.loads(audit_log.description)
            assert description["action"] == "subject_registration_update"
            assert description["student_id"] == str(self.student2.id)
            assert description["student_name"] == self.student2.full_name
            assert description["numerical_order"] == 2  # numerical_order from seasons_info
            assert len(description["subjects_registered"]) == 2
            assert str(self.subject.id) in description["subjects_registered"]
            assert str(self.subject2.id) in description["subjects_registered"]
            assert description["season"] == 3

            # Verify summary field is updated correctly after registration
            r_list = self.client.get(
                "/api/v1/subjects/registration",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r_list.status_code == 200
            resp_list = r_list.json()

            # Verify summary reflects new registrations
            assert "summary" in resp_list
            assert str(self.subject.id) in resp_list["summary"]
            assert str(self.subject2.id) in resp_list["summary"]
            # subject.id should have 2 students (student and student2)
            assert resp_list["summary"][str(self.subject.id)] == 2
            # subject2.id should have 1 student (student2)
            assert resp_list["summary"][str(self.subject2.id)] == 1

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

            # Verify no audit log was created for failed operation
            time.sleep(1)
            cursor = AuditLogModel._get_collection().find(
                {"type": AuditLogType.UPDATE, "endpoint": Endpoint.STUDENT}
            )
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            # Should still be 1 from the previous successful test
            assert len(audit_logs) == 1
