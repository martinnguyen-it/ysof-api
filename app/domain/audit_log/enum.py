from app.shared.utils.general import ExtendedEnum


class AuditLogType(str, ExtendedEnum):
    DELETE = "delete"
    UPDATE = "update"
    CREATE = "create"


class Endpoint(str, ExtendedEnum):
    ADMIN = "admin"
    AUTH = "auth"
    DOCUMENT = "document"
    GENERAL_TASK = "general_task"
    LECTURER = "lecturer"
    SEASON = "season"
    SUBJECT = "subject"
    UPLOAD = "upload"
