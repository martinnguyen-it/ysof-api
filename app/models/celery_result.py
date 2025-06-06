from mongoengine import (
    Document,
    StringField,
    DateTimeField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    DynamicField,
    BooleanField,
)

from app.config import settings


class ResultEmbedModel(EmbeddedDocument):
    tag = StringField()
    name = StringField()
    description = StringField()
    traceback = StringField()


class CeleryResultModel(Document):
    task_id = StringField(
        required=True,
    )
    result = EmbeddedDocumentField(ResultEmbedModel, required=True)
    date_done = DateTimeField()
    traceback = DynamicField()  # Allow any type
    children = DynamicField()  # Allow any type
    status = DynamicField()  # Allow any type
    group_id = StringField()
    parent_id = StringField()

    resolved = BooleanField()
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

    meta = {
        "collection": settings.MONGO_CELERY_COLLECTION,
        "indexes": [{"fields": ["task_id"], "unique": True}],
    }
