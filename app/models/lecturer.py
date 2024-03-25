import datetime
from mongoengine import Document, StringField, DateTimeField, ListField, IntField


class LecturerModel(Document):
    title = StringField(required=True)
    holy_name = StringField()
    full_name = StringField(required=True)
    avatar = StringField()
    information = StringField()
    contact = StringField()
    sessions = ListField(IntField())

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
        return super(LecturerModel, self).save(*args, **kwargs)

    meta = {
        "collection": "Lecturers",
        "indexes": ["full_name", "holy_name"],
        "allow_inheritance": True,
        "index_cls": False,
    }
