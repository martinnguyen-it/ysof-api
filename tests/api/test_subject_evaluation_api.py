import app.interfaces.api_v1.admin
import app.interfaces.api_v1.student
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
from app.models.student import StudentModel
from app.models.subject_evaluation import SubjectEvaluationModel, SubjectEvaluationQuestionModel
from app.models.manage_form import ManageFormModel
from app.domain.manage_form.enum import FormStatus, FormType


class TestSubjectEvaluationQuestionApi(unittest.TestCase):
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
        cls.subject_evaluation_question: SubjectEvaluationQuestionModel = SubjectEvaluationQuestionModel(
            subject=cls.subject,
            questions=[{"title": "Hình ảnh Thiên Chúa", "type": "text", "answers": []}],
        ).save()
        cls.subject_evaluation: SubjectEvaluationModel = SubjectEvaluationModel(
            quality={
                "focused_right_topic": "Trung lập",
                "practical_content": "Đồng ý",
                "benefit_in_life": "Hoàn toàn đồng ý",
                "duration": "Hoàn toàn đồng ý",
                "method": "Hoàn toàn đồng ý",
            },
            most_resonated="Bài giảng",
            invited="Sống",
            feedback_lecturer="Cảm ơn",
            satisfied=8,
            answers=["Xin ơn"],
            feedback_admin="Cảm ơn BTC",
            subject=cls.subject,
            student=cls.student2,
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    def test_create_subject_evaluation(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student.email)
            r = self.client.post(
                f"/api/v1/student/subjects/evaluation/{self.subject.id}",
                json={
                    "quality": {
                        "focused_right_topic": "Hoàn toàn đồng ý",
                        "practical_content": "Đồng ý",
                        "benefit_in_life": "Hoàn toàn đồng ý",
                        "duration": "Hoàn toàn đồng ý",
                        "method": "Hoàn toàn đồng ý",
                    },
                    "most_resonated": "Bài giảng hay",
                    "invited": "Sống",
                    "feedback_lecturer": "Cảm ơn",
                    "satisfied": 8,
                    "answers": ["Xin ơn"],
                    "feedback_admin": "Cảm ơn BTC",
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 400
            assert r.json()["detail"].startswith("Form chưa được mở")

            # Open form with dummy subject id
            manage_form = ManageFormModel(
                type=FormType.SUBJECT_EVALUATION,
                status=FormStatus.ACTIVE,
                data={"subject_id": "65f253a7fd143b81c101a63c"},
            ).save()
            r = self.client.post(
                f"/api/v1/student/subjects/evaluation/{self.subject.id}",
                json={
                    "quality": {
                        "focused_right_topic": "Hoàn toàn đồng ý",
                        "practical_content": "Đồng ý",
                        "benefit_in_life": "Hoàn toàn đồng ý",
                        "duration": "Hoàn toàn đồng ý",
                        "method": "Hoàn toàn đồng ý",
                    },
                    "most_resonated": "Bài giảng hay",
                    "invited": "Sống",
                    "feedback_lecturer": "Cảm ơn",
                    "satisfied": 8,
                    "answers": ["Xin ơn"],
                    "feedback_admin": "Cảm ơn BTC",
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 400
            assert r.json()["detail"] == "Form hiện tại không mở cho môn học này."

            ManageFormModel.objects(id=manage_form.id).update_one(
                type=FormType.SUBJECT_EVALUATION,
                status=FormStatus.ACTIVE,
                data={"subject_id": str(self.subject.id)},
                upsert=False,
            )
            manage_form.reload()

            r = self.client.post(
                f"/api/v1/student/subjects/evaluation/{self.subject.id}",
                json={
                    "quality": {
                        "focused_right_topic": "Hoàn toàn đồng ý",
                        "practical_content": "Đồng ý",
                        "benefit_in_life": "Hoàn toàn đồng ý",
                        "duration": "Hoàn toàn đồng ý",
                        "method": "Hoàn toàn đồng ý",
                    },
                    "most_resonated": "Bài giảng hay",
                    "invited": "Sống",
                    "feedback_lecturer": "Cảm ơn",
                    "satisfied": 8,
                    "answers": ["Xin ơn", "Xin ơn"],
                    "feedback_admin": "Cảm ơn BTC",
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            # Fail cause subject questions just only have one question, but number answers in payload is two
            assert r.status_code == 400
            assert r.json()["detail"] == "Câu trả lời không hợp lệ."

            r = self.client.post(
                f"/api/v1/student/subjects/evaluation/{self.subject.id}",
                json={
                    "quality": {
                        "focused_right_topic": "Hoàn toàn đồng ý",
                        "practical_content": "Đồng ý",
                        "benefit_in_life": "Hoàn toàn đồng ý",
                        "duration": "Hoàn toàn đồng ý",
                        "method": "Hoàn toàn đồng ý",
                    },
                    "most_resonated": "Bài giảng hay",
                    "invited": "Sống",
                    "feedback_lecturer": "Cảm ơn",
                    "satisfied": 8,
                    "answers": ["Xin ơn"],
                    "feedback_admin": "Cảm ơn BTC",
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["most_resonated"] == "Bài giảng hay"
            assert resp["subject"]
            assert "student" not in resp
            assert resp["quality"]

    def test_update_subject_evaluation(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student2.email)
            r = self.client.patch(
                f"/api/v1/student/subjects/evaluation/{self.subject.id}",
                json={
                    "most_resonated": "Updated",
                },
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["most_resonated"] == "Updated"

    def test_get_subject_evaluation_by_subject_id(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student2.email)
            r = self.client.get(
                f"/api/v1/student/subjects/evaluation/{self.subject.id}",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert resp["feedback_lecturer"] == "Cảm ơn"

    def test_get_all_subject_evaluation(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student2.email)
            r = self.client.get(
                "/api/v1/student/subjects/evaluation",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            resp = r.json()
            assert len(resp) == 1
