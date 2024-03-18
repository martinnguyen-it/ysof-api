import datetime
from mongoengine import Document, StringField, DateTimeField, IntField, ListField, ReferenceField


class DocumentModel(Document):
    file_id = StringField(required=True)
    mimeType = StringField()
    name = StringField(required=True)
    thumbnailLink = StringField()

    role = StringField(required=True)
    type = StringField(required=True)
    description = StringField()
    label = ListField(StringField())
    session = IntField(required=True)

    author = ReferenceField("AdminModel", required=True)

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
            self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()
        return super(DocumentModel, self).save(*args, **kwargs)

    meta = {
        "collection": "Documents",
        "indexes": ["file_id", "type", "session"],
        "allow_inheritance": True,
        "index_cls": False,
    }
