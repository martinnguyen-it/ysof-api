import app.interfaces.api_v1.admin
import app.interfaces.api_v1.student
import time
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
from app.models.season import SeasonModel
from app.models.audit_log import AuditLogModel
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.models.student import StudentModel
from app.models.subject_evaluation import SubjectEvaluationQuestionModel


class TestSubjectEvaluationQuestionApi(unittest.TestCase):
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
        cls.subject_evaluation_question: SubjectEvaluationQuestionModel = SubjectEvaluationQuestionModel(
            subject=cls.subject2,
            questions=[{"title": "Hình ảnh Thiên Chúa", "type": "text", "answers": []}],
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    def test_create_subject_evaluation_question(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user2.email)
            r = self.client.post(
                f"/api/v1/subjects/evaluation-questions/{self.subject.id}",
                json={"questions": [{"title": "Đâu là hình ảnh của Thiên Chúa ?", "type": "text"}]},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 403

            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.post(
                f"/api/v1/subjects/evaluation-questions/{self.subject.id}",
                json={"questions": [{"title": "Đâu là hình ảnh của Thiên Chúa ?", "type": "text"}]},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            resp = r.json()
            assert resp["questions"][0]["title"] == "Đâu là hình ảnh của Thiên Chúa ?"

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find(
                {"type": AuditLogType.CREATE, "endpoint": Endpoint.SUBJECT_EVALUATION_QUESTION}
            )
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1

    def test_update_subject_evaluation_question(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user2.email)
            r = self.client.patch(
                f"/api/v1/subjects/evaluation-questions/{self.subject.id}",
                json={"questions": [{"title": "Đâu là hình ảnh của Thiên Chúa 2?", "type": "text"}]},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 403

            mock_token.return_value = TokenData(email=self.user.email)
            r = self.client.patch(
                f"/api/v1/subjects/evaluation-questions/{self.subject.id}",
                json={"questions": [{"title": "Đâu là hình ảnh của Thiên Chúa 2?", "type": "text"}]},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            resp = r.json()
            assert resp["questions"][0]["title"] == "Đâu là hình ảnh của Thiên Chúa 2?"

            time.sleep(1)
            cursor = AuditLogModel._get_collection().find(
                {"type": AuditLogType.UPDATE, "endpoint": Endpoint.SUBJECT_EVALUATION_QUESTION}
            )
            audit_logs = [AuditLogModel.from_mongo(doc) for doc in cursor] if cursor else []
            assert len(audit_logs) == 1

    def test_get_subject_evaluation_question(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user2.email)
            r = self.client.get(
                f"/api/v1/subjects/evaluation-questions/{self.subject2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["questions"][0]["title"] == self.subject_evaluation_question.questions[0]["title"]

            mock_token.return_value = TokenData(email=self.student.email)
            r = self.client.get(
                f"/api/v1/student/subjects/evaluation-questions/{self.subject2.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["questions"][0]["title"] == self.subject_evaluation_question.questions[0]["title"]
