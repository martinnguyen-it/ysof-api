import datetime
from mongoengine import Document, StringField, EmailField, DateTimeField, DictField, IntField


class UserModel(Document):
    numerical_order = IntField(required=True, unique=True)
    group = IntField(required=True)
    holy_name = StringField(required=True)
    full_name = StringField(required=True)
    sex = StringField()
    date_of_birth = DateTimeField()
    address = DictField()
    phone_number = StringField()

    email = EmailField(required=True)
    password = StringField()
    avatar = StringField()

    education = StringField()
    job = StringField()

    note = StringField()

    current_season = StringField()

    status = StringField(required=True)
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
        return super(UserModel, self).save(*args, **kwargs)

    meta = {
        "collection": "Users",
        "indexes": ["email", "status"],
        "allow_inheritance": True,
        "index_cls": False,
    }
