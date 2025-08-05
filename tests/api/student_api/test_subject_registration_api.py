import pytest
import unittest
import time
from unittest.mock import patch

from mongoengine import connect, disconnect
from fastapi.testclient import TestClient

from app.main import app
import mongomock

from app.infra.security.security_service import (
    TokenData,
    get_password_hash,
)
from app.models.season import SeasonModel
from app.models.student import SeasonInfo, StudentModel
from app.models.subject import SubjectModel
from app.models.lecturer import LecturerModel
from app.models.manage_form import ManageFormModel
from app.domain.manage_form.enum import FormStatus, FormType
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

    @classmethod
    def tearDownClass(cls):
        disconnect()

    @pytest.mark.order(1)
    def test_student_registration(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student.email)

            r = self.client.post(
                "/api/v1/student/subjects/registration",
                json={"subjects": [str(self.subject.id), str(self.subject2.id)]},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 400
            assert r.json()["detail"].startswith("Form chưa được mở")

            ManageFormModel(type=FormType.SUBJECT_REGISTRATION, status=FormStatus.ACTIVE).save()

            r = self.client.post(
                "/api/v1/student/subjects/registration",
                json={"subjects": [str(self.subject.id), str(self.subject2.id)]},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["student_id"] == str(self.student.id)
            assert len(resp["subjects_registration"]) == 2

            # Verify no audit log was created for student self-registration
            time.sleep(1)
            cursor = AuditLogModel._get_collection().find(
                {"type": AuditLogType.UPDATE, "endpoint": Endpoint.STUDENT}
            )
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 0

    @pytest.mark.order(2)
    def test_get_student_registration_by_self(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student.email)
            r = self.client.get(
                "/api/v1/student/subjects/registration",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            resp = r.json()
            assert r.status_code == 200
            assert resp["student_id"] == str(self.student.id)
            assert len(resp["subjects_registration"]) == 2
