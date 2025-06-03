from mongoengine import Document, ReferenceField, BooleanField


class SubjectRegistrationModel(Document):
    student = ReferenceField("StudentModel", required=True)
    subject = ReferenceField("SubjectModel", required=True)
    attend_zoom = BooleanField()

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
        "collection": "SubjectRegistration",
        "indexes": [{"fields": ["student", "subject"], "unique": True}],
        "allow_inheritance": True,
        "index_cls": False,
    }
