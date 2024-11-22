import datetime
from mongoengine import (
    Document,
    StringField,
    EmailField,
    DateTimeField,
    IntField,
    DateField,
    EmbeddedDocument,
    EmbeddedDocumentListField,
    Q,
)

from app.shared.common_exception import CustomException


class SeasonInfo(EmbeddedDocument):
    numerical_order = IntField(required=True)
    group = IntField(required=True)
    season = IntField(required=True)

    meta = {"indexes": [{"fields": ("numerical_order", "season"), "unique": True}]}


class StudentModel(Document):
    seasons_info = EmbeddedDocumentListField(SeasonInfo)
    email = EmailField(required=True, unique=True)

    holy_name = StringField(required=True)
    full_name = StringField(required=True)
    sex = StringField()
    date_of_birth = DateField()
    origin_address = StringField()
    diocese = StringField()
    phone_number = StringField()

    password = StringField(required=True)
    avatar = StringField()

    education = StringField()
    job = StringField()

    note = StringField()

    status = StringField(required=True)
    created_at = DateTimeField()
    updated_at = DateTimeField()

    def clean(self):
        if len(self.seasons_info) == 0:
            raise CustomException("Học viên cần thuộc ít nhất một mùa.")

        # Ensure uniqueness of (season, numerical_order) across all students and season unique
        # in each student
        seen_seasons = set()
        for season_doc in self.seasons_info:
            # Check for duplicate seasons within the same student
            if season_doc.season in seen_seasons:
                raise CustomException(
                    f"Học viên này ({self.email}) đã đăng ký mùa {season_doc.season}."
                )
            seen_seasons.add(season_doc.season)

            # Check that no other student has the same (season, numerical_order)
            existing_student = StudentModel.objects.filter(
                Q(id__ne=self.id)  # Exclude the current document
                & Q(
                    seasons_info__elemMatch={
                        "season": season_doc.season,
                        "numerical_order": season_doc.numerical_order,
                    }
                )
            ).first()

            if existing_student:
                raise CustomException(
                    f"Đã tồn tại một học viên khác có MSHV {season_doc.numerical_order} "
                    f"ở mùa {season_doc.season}."
                )

    @classmethod
    def from_mongo(cls, data: dict, id_str=False):
        """We must convert _id into "id"."""
        if not data:
            return data
        id = data.pop("_id", None) if not id_str else str(data.pop("_id", None))
        if "_cls" in data:
            data.pop("_cls", None)
        return cls(**dict(data, id=id))

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()
        return super(StudentModel, self).save(*args, **kwargs)

    meta = {
        "collection": "Students",
        "indexes": [
            "email",
            "status",
            {"fields": ("seasons_info.numerical_order", "seasons_info.season"), "unique": True},
        ],
        "allow_inheritance": True,
        "index_cls": False,
    }
