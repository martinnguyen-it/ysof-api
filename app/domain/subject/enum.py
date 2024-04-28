from app.shared.utils.general import ExtendedEnum


class StatusSubjectEnum(str, ExtendedEnum):
    INIT = "init"
    SENT_STUDENT = "sent_student"
    SENT_EVALUATION = "sent_evaluation"
