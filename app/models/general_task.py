from datetime import datetime, timezone
from mongoengine import Document, StringField, DateTimeField, IntField, ListField, ReferenceField


class GeneralTaskModel(Document):
    title = StringField(required=True)
    short_desc = StringField()
    description = StringField(required=True)
    start_at = DateTimeField(required=True)
    end_at = DateTimeField(required=True)

    season = IntField(required=True)
    role = StringField(required=True)
    type = StringField(required=True)
    label = ListField(StringField())

    author = ReferenceField("AdminModel", required=True)
    attachments = ListField(ReferenceField("DocumentModel"))

    created_at = DateTimeField()
    updated_at = DateTimeField()

    @classmethod
    def from_mongo(cls, data: dict, id_str=False):
        """We must convert _id into "id". """
        if not data:
            return data
        id = data.pop("_id", None) if not id_str else str(
            data.pop("_id", None))
        if "_cls" in data:
            data.pop("_cls", None)
        return cls(**dict(data, id=id))

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        return super(GeneralTaskModel, self).save(*args, **kwargs)

    meta = {
        "collection": "GeneralTasks",
        "indexes": ["title", "short_desc", "end_at"],
        "allow_inheritance": True,
        "index_cls": False,
    }
