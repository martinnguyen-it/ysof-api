from app.shared.utils.general import ExtendedEnum


class FormType(str, ExtendedEnum):
    SUBJECT_REGISTRATION = "subject_registration"


class FormStatus(str, ExtendedEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"
