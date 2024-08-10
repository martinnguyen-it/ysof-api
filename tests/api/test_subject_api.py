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
from app.models.student import StudentModel
from app.models.subject_registration import SubjectRegistrationModel
from app.models.document import DocumentModel
from app.domain.document.enum import DocumentType


today = date.today() + timedelta(days=365)
mockData = {
    "title": "Data mock",
    "start_at": f"{today.year}-01-01",
    "subdivision": "Kinh thánh",
    "code": "Y10.1",
    "question_url": "abc.com",
}


class TestSubjectApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect()
        connect("mongoenginetest", host="mongodb://localhost:1234", mongo_client_class=mongomock.MongoClient)
        cls.client = TestClient(app)
        cls.season: SeasonModel = SeasonModel(
            title="CÙNG GIÁO HỘI, NGƯỜI TRẺ BƯỚC ĐI TRONG HY VỌNG", academic_year="2023-2024", season=3, is_current=True
        ).save()
        cls.user: AdminModel = AdminModel(
            status="active",
            roles=[
                "admin",
            ],
            holy_name="Martin",
            phone_number=["0123456789"],
            current_season=3,
            seasons=[3],
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
            phone_number=["0123456789"],
            current_season=3,
            seasons=[3],
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
            phone_number=["0123456789"],
            current_season=3,
            seasons=[3],
            email="user2@example.com",
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
        cls.document = DocumentModel(
            file_id="1hXt8WI3g6p8YUtN2gR35yA-gO_fE2vD3",
            mimeType="image/jpeg",
            name="Tài liệu học",
            role="bhv",
            type=DocumentType.STUDENT,
            label=["string"],
            season=3,
            author=cls.user,
        ).save()
        cls.document2 = DocumentModel(
            file_id="1hXt8WI3g6p8YUtN2gR35yA-gO_fE2vD3",
            mimeType="image/jpeg",
            name="Tài liệu học",
            role="bhv",
            type=DocumentType.COMMON,
            label=["string"],
            season=3,
            author=cls.user,
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
        cls.subject2: SubjectModel = SubjectModel(
            title="Môn học 2",
            start_at="2024-03-27",
            subdivision="string",
            code="string",
            question_url="string",
            zoom={"meeting_id": 0, "pass_code": "string", "link": "string"},
            documents_url=["string"],
            status="init",
            attachments=[cls.document],
            lecturer=cls.lecturer,
            season=3,
        ).save()
        cls.subject3: SubjectModel = SubjectModel(
            title="Môn học 3",
            start_at="2024-03-27",
            subdivision="string",
            code="string",
            question_url="string",
            zoom={"meeting_id": 0, "pass_code": "string", "link": "string"},
            documents_url=["string"],
            attachments=[cls.document],
            status="init",
            lecturer=cls.lecturer,
            season=2,
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
        cls.subject_registration: SubjectRegistrationModel = SubjectRegistrationModel(
            subject=cls.subject.id, student=cls.student.id
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    @pytest.mark.order(2)
    def test_create_subject(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user2.email)

            r = self.client.post(
                "/api/v1/subjects",
                json={
                    "title": "Học hỏi",
                    "start_at": "2024-03-26",
                    "subdivision": "Kinh thánh",
                    "code": "Y10.1",
                    "question_url": "abc.com",
                    "zoom": {"meeting_id": 912424124, "pass_code": "123456", "link": "xyz.com"},
                    "documents_url": ["123.com"],
                    "lecturer": str(self.lecturer.id),
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
                    "start_at": "2024-03-26",
                    "subdivision": "Kinh thánh",
                    "code": "Y10.1",
                    "question_url": "abc.com",
                    "zoom": {"meeting_id": 912424124, "pass_code": "123456", "link": "xyz.com"},
                    "documents_url": ["123.com"],
                    "lecturer": str(self.lecturer.id),
                    "attachments": [str(self.lecturer.id)],
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 404
            assert r.json()["detail"].startswith("Tài liệu đính kèm không tồn tại hoặc thuộc mùa cũ")

            r = self.client.post(
                "/api/v1/subjects",
                json={
                    "title": "Học hỏi",
                    "start_at": "2024-03-26",
                    "subdivision": "Kinh thánh",
                    "code": "Y10.1",
                    "question_url": "abc.com",
                    "zoom": {"meeting_id": 912424124, "pass_code": "123456", "link": "xyz.com"},
                    "documents_url": ["123.com"],
                    "lecturer": str(self.lecturer.id),
                    "attachments": [str(self.document.id), str(self.document2.id)],
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 400
            assert r.json()["detail"].startswith("Vui lòng chỉ chọn tài liệu đính kèm dành cho học viên")

            r = self.client.post(
                "/api/v1/subjects",
                json={
                    "title": mockData["title"],
                    "start_at": mockData["start_at"],
                    "subdivision": mockData["subdivision"],
                    "code": mockData["code"],
                    "question_url": mockData["question_url"],
                    "zoom": {"meeting_id": 912424124, "pass_code": "123456", "link": "xyz.com"},
                    "documents_url": ["123.com"],
                    "lecturer": str(self.lecturer.id),
                    "attachments": [str(self.document.id)],
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            resp = r.json()
            assert r.status_code == 200
            assert resp["title"] == mockData["title"]
            assert resp["lecturer"]["full_name"] == self.lecturer.full_name
            assert "attachments" in resp
            assert "abstract" in resp
            assert len(resp["attachments"]) == 1

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find({"type": AuditLogType.CREATE, "endpoint": Endpoint.SUBJECT})
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1

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
            """_summary_
                len(resp) == 2
                Because mock 3 subjects, but one subject is season 2, one subject deleted
                Default get list subject is current season
            """
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
            doc: SubjectModel = SubjectModel.objects(id=r.json().get("id")).get()
            assert doc.title == self.subject.title
            assert doc.code == self.subject.code

    def test_update_subject_by_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user1.email)
            r = self.client.put(
                f"/api/v1/subjects/{self.subject3.id}",
                json={"title": "Updated"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 403

            r = self.client.put(
                f"/api/v1/subjects/{self.subject.id}",
                json={"title": "Updated"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            doc: SubjectModel = SubjectModel.objects(id=r.json().get("id")).get()
            assert doc.title == "Updated"

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find({"type": AuditLogType.UPDATE, "endpoint": Endpoint.SUBJECT})
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1

    @pytest.mark.order(1)
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
                f"/api/v1/subjects/{self.subject.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 400
            assert r.json().get("detail").startswith("Không thể xóa")

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

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find({"type": AuditLogType.DELETE, "endpoint": Endpoint.SUBJECT})
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1

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

    def test_get_next_most_recent(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user1.email)
            r = self.client.get(
                "/api/v1/subjects/next-most-recent",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            resp = r.json()
            print(resp)
            assert r.status_code == 200
            assert resp["title"] == mockData["title"]
