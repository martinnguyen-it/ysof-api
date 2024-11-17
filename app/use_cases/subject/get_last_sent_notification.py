from fastapi import Depends
from app.shared import use_case
from app.domain.subject.entity import Subject, SubjectInDB
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel
from app.domain.lecturer.entity import Lecturer, LecturerInDB
from app.domain.document.entity import AdminInDocument, Document, DocumentInDB
from app.domain.admin.entity import AdminInDB
from datetime import datetime
from app.shared.utils.general import get_current_season_value
from app.domain.subject.enum import StatusSubjectEnum


class GetSubjectLastSentNotificationUseCase(use_case.UseCase):
    def __init__(self, subject_repository: SubjectRepository = Depends(SubjectRepository)):
        self.subject_repository = subject_repository

    def process_request(self):
        current_season = get_current_season_value()
        subjects: list[SubjectModel] = self.subject_repository.list(
            match_pipeline={
                "start_at": {"$lte": datetime.now()},
                "status": StatusSubjectEnum.SENT_NOTIFICATION,
                "season": current_season,
            },
            sort={"start_at": -1},
            page_index=1,
            page_size=1,
        )
        if len(subjects) == 0:
            return {"message": "Không có buổi học nào cũ chưa hoàn thành"}

        return Subject(
            **SubjectInDB.model_validate(subjects[0]).model_dump(
                exclude=({"lecturer", "attachments"})
            ),
            lecturer=Lecturer(**LecturerInDB.model_validate(subjects[0].lecturer).model_dump()),
            attachments=[
                Document(
                    **DocumentInDB.model_validate(doc).model_dump(exclude=({"author"})),
                    author=AdminInDocument(**AdminInDB.model_validate(doc.author).model_dump()),
                )
                for doc in subjects[0].attachments
            ],
        )
