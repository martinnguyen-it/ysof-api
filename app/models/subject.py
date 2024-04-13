from datetime import datetime, timezone
from mongoengine import (
    Document,
    StringField,
    DateTimeField,
    IntField,
    ListField,
    DateField,
    ReferenceField,
    EmbeddedDocument,
    EmbeddedDocumentField,
)


class ZoomInfo(EmbeddedDocument):
    meeting_id = IntField()
    pass_code = StringField()
    link = StringField()


class SubjectModel(Document):
    title = StringField(required=True)
    start_at = DateField(required=True)
    subdivision = StringField(required=True)
    lecturer = ReferenceField("LecturerModel", required=True)
    code = StringField(required=True)
    question_url = StringField()
    documents_url = ListField(StringField())
    zoom = EmbeddedDocumentField(ZoomInfo)

    season = IntField(required=True)
    created_at = DateTimeField()
    updated_at = DateTimeField()

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
            self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        return super(SubjectModel, self).save(*args, **kwargs)

    meta = {
        "collection": "Subjects",
        "indexes": ["title", "subdivision", "code"],
        "allow_inheritance": True,
        "index_cls": False,
    }
