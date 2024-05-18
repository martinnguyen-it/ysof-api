from fastapi import Depends
from app.shared import use_case
from app.domain.subject.entity import Subject, SubjectInDB
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel
from app.domain.lecturer.entity import Lecturer, LecturerInDB
from app.domain.document.entity import AdminInDocument, Document, DocumentInDB
from app.domain.admin.entity import AdminInDB
from datetime import datetime, date
from app.shared.utils.general import get_current_season_value


class GetSubjectNextMostRecentUseCase(use_case.UseCase):
    def __init__(self, subject_repository: SubjectRepository = Depends(SubjectRepository)):
        self.subject_repository = subject_repository

    def process_request(self):
        current_season = get_current_season_value()
        today = date.today()
        subjects: list[SubjectModel] = self.subject_repository.list(
            match_pipeline={
                "start_at": {"$gte": datetime(today.year, today.month, today.day)},
                "season": current_season,
            },
            sort={"start_at": 1},
            page_index=1,
            page_size=1,
        )
        if len(subjects) == 0:
            return {"message": "Không còn buổi học nào tiếp theo"}

        return Subject(
            **SubjectInDB.model_validate(subjects[0]).model_dump(exclude=({"lecturer", "attachments"})),
            lecturer=Lecturer(**LecturerInDB.model_validate(subjects[0].lecturer).model_dump()),
            attachments=[
                Document(
                    **DocumentInDB.model_validate(doc).model_dump(exclude=({"author"})),
                    author=AdminInDocument(**AdminInDB.model_validate(doc.author).model_dump()),
                )
                for doc in subjects[0].attachments
            ],
        )
