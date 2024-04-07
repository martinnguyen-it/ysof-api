import datetime
from mongoengine import Document, StringField, EmailField, DateTimeField, IntField


class StudentModel(Document):
    numerical_order = IntField(required=True, unique=True)
    group = IntField(required=True)
    holy_name = StringField(required=True)
    full_name = StringField(required=True)
    sex = StringField()
    date_of_birth = DateTimeField()
    origin_address = StringField()
    diocese = StringField()
    phone_number = StringField()

    email = EmailField(required=True, unique=True)
    password = StringField(required=True)
    avatar = StringField()

    education = StringField()
    job = StringField()

    note = StringField()

    current_season = IntField(required=True)
    status = StringField(required=True)
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
            self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()
        return super(StudentModel, self).save(*args, **kwargs)

    meta = {
        "collection": "Students",
        "indexes": ["email", "status", "full_name", "holy_name", "numerical_order"],
        "allow_inheritance": True,
        "index_cls": False,
    }
