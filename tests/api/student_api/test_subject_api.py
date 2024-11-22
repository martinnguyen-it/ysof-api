import app.interfaces.api_v1.admin
from datetime import date, timedelta
import time
import unittest
from unittest.mock import patch
import pytest

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
from app.models.audit_log import AuditLogModel
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.models.student import SeasonInfo, StudentModel
from app.models.subject_registration import SubjectRegistrationModel
from app.models.document import DocumentModel
from app.domain.document.enum import DocumentType
from app.models.manage_form import ManageFormModel
from app.domain.manage_form.enum import FormStatus, FormType
from app.domain.subject.enum import StatusSubjectEnum


today = date.today()
mock_data_most_recent = {
    "title": "Data mock",
    "start_at": f"{(today+timedelta(days=365)).year}-01-01",
    "subdivision": "Kinh thánh",
    "code": "Y10.1",
    "question_url": "abc.com",
}

mock_data_send_notification = {
    "title": "Data mock",
    "start_at": f"{(today-timedelta(days=365)).year}-01-01",
    "subdivision": "Kinh thánh",
    "code": "Y10.2",
    "question_url": "abc.com",
}


class TestSubjectApi(unittest.TestCase):
    id_subject_send_notification = ""

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
        cls.document = DocumentModel(
            file_id="1hXt8WI3g6p8YUtN2gR35yA-gO_fE2vD3",
            mimeType="image/jpeg",
            name="Tài liệu học",
            role="bhv",
            type=DocumentType.STUDENT,
            label=["string"],
            season=3,
            author=cls.admin,
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
            attachments=[cls.document],
            status="init",
            season=3,
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

    @classmethod
    def tearDownClass(cls):
        disconnect()

    def test_student_get_subject_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student.email)
            r = self.client.get(
                f"/api/v1/student/subjects/{self.subject.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert "zoom" not in resp
            assert resp["title"] == self.subject.title
            assert "contact" not in resp["lecturer"]
            assert "abstract" in resp

            assert resp["lecturer"]["full_name"] == self.subject.lecturer.full_name
            assert resp["attachments"][0]["name"] == self.subject.attachments[0].name

    def test_student_get_all_subjects(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student.email)
            r = self.client.get(
                "/api/v1/student/subjects",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            resp = r.json()
            assert r.status_code == 200
            assert isinstance(resp, list)
            assert "zoom" not in resp[0]
            assert resp[0]["title"] == self.subject.title
            assert "contact" not in resp[0]["lecturer"]
            assert "abstract" in resp[0]

            assert resp[0]["lecturer"]["full_name"] == self.subject.lecturer.full_name
            assert resp[0]["attachments"][0]["name"] == self.subject.attachments[0].name
