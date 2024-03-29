import datetime
from mongoengine import Document, StringField, DateTimeField, BooleanField, IntField


class SeasonModel(Document):
    title = StringField(required=True)
    season = IntField(required=True, unique=True)
    is_current = BooleanField(required=True)
    description = StringField()
    academic_year = StringField()

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
        return super(SeasonModel, self).save(*args, **kwargs)

    meta = {
        "collection": "Seasons",
        "indexes": ["season", "is_current"],
        "allow_inheritance": True,
        "index_cls": False,
    }
