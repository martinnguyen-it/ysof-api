from app.shared.utils.general import ExtendedEnum


class FormType(str, ExtendedEnum):
    SUBJECT_REGISTRATION = "subject_registration"
    SUBJECT_EVALUATION = "subject_evaluation"
    SUBJECT_ABSENT = "subject_absent"


class FormStatus(str, ExtendedEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"
