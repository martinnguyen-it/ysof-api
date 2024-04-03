from datetime import datetime, timezone
from mongoengine import (Document, StringField, EmailField, DateTimeField, EmbeddedDocumentField,
                         ListField, IntField, EmbeddedDocument)


class Address(EmbeddedDocument):
    current = StringField()
    original = StringField()
    diocese = StringField()


class AdminModel(Document):
    email = EmailField(required=True, unique=True)
    status = StringField(required=True)
    roles = ListField(StringField(), required=True)
    full_name = StringField(required=True)
    holy_name = StringField(required=True)
    phone_number = ListField(StringField())
    password = StringField(required=True)
    address = EmbeddedDocumentField(Address)
    date_of_birth = DateTimeField()
    facebook = StringField()
    current_season = IntField()
    seasons = ListField(IntField())

    avatar = StringField()
    created_at = DateTimeField(required=True)
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
        return super(AdminModel, self).save(*args, **kwargs)

    meta = {
        "collection": "Admins",
        "indexes": ["email", "status", "current_season", "full_name", "holy_name"],
        "allow_inheritance": True,
        "index_cls": False,
    }
