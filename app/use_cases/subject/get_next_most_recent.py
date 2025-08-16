from fastapi import Depends
from app.shared import response_object, use_case
from app.domain.subject.entity import Subject, SubjectInDB
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel
from app.domain.lecturer.entity import Lecturer, LecturerInDB
from app.domain.document.entity import AdminInDocument, Document, DocumentInDB
from app.domain.admin.entity import AdminInDB
from datetime import datetime, date
from app.shared.utils.general import get_current_season_value, get_subject_extra_emails_redis_key
from app.config.redis import RedisDependency


class GetSubjectNextMostRecentUseCase(use_case.UseCase):
    def __init__(
        self,
        redis_client: RedisDependency,
        subject_repository: SubjectRepository = Depends(SubjectRepository),
    ):
        self.subject_repository = subject_repository
        self.redis_client = redis_client

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
            return response_object.ResponseFailure.build_not_found_error(
                "Không còn buổi học nào tiếp theo"
            )

        # Fetch extra emails from Redis if they exist
        subject_data = subjects[0]
        redis_key = get_subject_extra_emails_redis_key(str(subject_data.id))
        extra_emails = None
        if self.redis_client.exists(redis_key):
            extra_emails_set = self.redis_client.smembers(redis_key)
            if extra_emails_set:
                extra_emails = extra_emails_set

        return Subject(
            **SubjectInDB.model_validate(subject_data).model_dump(
                exclude=({"lecturer", "attachments"})
            ),
            lecturer=Lecturer(**LecturerInDB.model_validate(subject_data.lecturer).model_dump()),
            attachments=[
                Document(
                    **DocumentInDB.model_validate(doc).model_dump(exclude=({"author"})),
                    author=AdminInDocument(**AdminInDB.model_validate(doc.author).model_dump()),
                )
                for doc in subject_data.attachments
            ],
            extra_emails=extra_emails,
        )
