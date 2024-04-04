from datetime import datetime, timezone
from mongoengine import Document, StringField, DateTimeField, IntField, ReferenceField, ListField


class AuditLogModel(Document):
    type = StringField(required=True)
    endpoint = StringField(required=True)
    author = ReferenceField("AdminModel")
    author_name = StringField(required=True)
    author_email = StringField(required=True)
    author_roles = ListField(StringField(), required=True)
    description = StringField()

    season = IntField(required=True)
    created_at = DateTimeField()

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
        self.created_at = datetime.now(timezone.utc)
        return super(AuditLogModel, self).save(*args, **kwargs)

    meta = {
        "collection": "Logs",
        "indexes": ["endpoint", "type", "author_name", "season"],
        "allow_inheritance": True,
        "index_cls": False,
    }
