from datetime import datetime, timezone
from mongoengine import (
    Document,
    ReferenceField,
    EmbeddedDocumentField,
    EmbeddedDocument,
    IntField,
    StringField,
    ListField,
    DateTimeField,
)


class QualityDocument(EmbeddedDocument):
    focused_right_topic = StringField(required=True)
    practical_content = StringField(required=True)
    benefit_in_life = StringField(required=True)
    duration = StringField(required=True)
    method = StringField(required=True)


class SubjectEvaluationModel(Document):
    student = ReferenceField("StudentModel", required=True)
    subject = ReferenceField("SubjectModel", required=True)

    quality = EmbeddedDocumentField(QualityDocument, required=True)
    most_resonated = StringField(required=True)
    invited = StringField(required=True)
    feedback_lecturer = StringField(required=True)
    satisfied = IntField(required=True)

    answers = ListField()

    feedback_admin = StringField()
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
        return super(SubjectEvaluationModel, self).save(*args, **kwargs)

    meta = {
        "collection": "SubjectRegistration",
        "indexes": [{"fields": ["student", "subject"], "unique": True}],
        "allow_inheritance": True,
        "index_cls": False,
    }


class QuestionDocument(EmbeddedDocument):
    title = StringField(required=True)
    type = StringField(required=True)
    answers = ListField(StringField())


class SubjectEvaluationQuestionModel(Document):
    subject = ReferenceField("SubjectModel", required=True, unique=True)
    questions = ListField(EmbeddedDocumentField(QuestionDocument))

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
        return super(SubjectEvaluationQuestionModel, self).save(*args, **kwargs)

    meta = {
        "collection": "SubjectEvaluationQuestion",
        "indexes": ["subject"],
        "allow_inheritance": True,
        "index_cls": False,
    }
