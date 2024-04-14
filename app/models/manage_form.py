from datetime import datetime, timezone
from mongoengine import Document, StringField, DateTimeField, DictField


class ManageFormModel(Document):
    status = StringField(required=True)
    type = StringField(required=True)
    data = DictField()

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
        return super(ManageFormModel, self).save(*args, **kwargs)

    meta = {
        "collection": "ManageForms",
        "indexes": ["type", "status"],
        "allow_inheritance": True,
        "index_cls": False,
    }
