from app.shared.utils.general import ExtendedEnum


class AuditLogType(str, ExtendedEnum):
    DELETE = "delete"
    UPDATE = "update"
    CREATE = "create"
    IMPORT = "import"


class Endpoint(str, ExtendedEnum):
    ADMIN = "admin"
    AUTH = "auth"
    DOCUMENT = "document"
    GENERAL_TASK = "general_task"
    LECTURER = "lecturer"
    SEASON = "season"
    SUBJECT = "subject"
    SUBJECT_EVALUATION_QUESTION = "subject_evaluation_questions"
    UPLOAD = "upload"
    STUDENT = "student"
    MANAGE_FORM = "manage_form"
    ABSENT = "absent"
