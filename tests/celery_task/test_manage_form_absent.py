import unittest
from mongoengine import connect, disconnect
import mongomock
import pytest

from app.models.season import SeasonModel
from app.models.lecturer import LecturerModel
from app.models.subject import SubjectModel
from app.infra.tasks.periodic.manage_form_absent import (
    close_form_absent_task,
    open_form_absent_task,
)
from app.models.manage_form import ManageFormModel
from app.domain.manage_form.enum import FormStatus, FormType
from datetime import date, timedelta


class TestAdminApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect()
        connect(
            "mongoenginetest",
            host="mongodb://localhost:1234",
            mongo_client_class=mongomock.MongoClient,
        )
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
        cls.subject: SubjectModel = SubjectModel(
            title="Môn học 1",
            start_at=date.today() + timedelta(days=6),
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
    def test_open_form_absent_task(self):
        open_form_absent_task()
        form: ManageFormModel | None = ManageFormModel.objects(type=FormType.SUBJECT_ABSENT).get()
        assert form
        assert form.status == FormStatus.ACTIVE
        assert "subject_id" in form.data
        assert form.data["subject_id"] == str(self.subject.id)

    @pytest.mark.order(2)
    def test_close_form_absent_task(self):
        close_form_absent_task()
        form: ManageFormModel | None = ManageFormModel.objects(type=FormType.SUBJECT_ABSENT).get()
        assert form
        assert form.status == FormStatus.CLOSED
