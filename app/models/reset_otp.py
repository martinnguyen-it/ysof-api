from datetime import datetime, timezone
from mongoengine import Document, StringField, EmailField, DateTimeField, IntField


class ResetOTPModel(Document):
    email = EmailField(required=True)
    otp = StringField(required=True)
    user_type = StringField(required=True, choices=["admin", "student"])
    expires_at = DateTimeField(required=True)
    is_used = IntField(default=0)  # 0: not used, 1: used
    created_at = DateTimeField(required=True)
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
        return super(ResetOTPModel, self).save(*args, **kwargs)

    def is_expired(self):
        # Ensure both datetimes are timezone-aware
        current_time = datetime.now(timezone.utc)
        if self.expires_at.tzinfo is None:
            # If expires_at is naive, assume it's UTC
            expires_at_aware = self.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at_aware = self.expires_at
        return current_time > expires_at_aware

    def mark_as_used(self):
        self.is_used = 1
        self.save()

    meta = {
        "collection": "ResetOTPs",
        "indexes": [
            {"fields": ["email", "user_type"], "unique": True},
            "expires_at",
            "is_used",
        ],
        "allow_inheritance": True,
        "index_cls": False,
    }
