from app.shared.utils.general import ExtendedEnum


class StatusSubjectEnum(str, ExtendedEnum):
    INIT = "init"
    SENT_NOTIFICATION = "sent_notification"
    SENT_EVALUATION = "sent_evaluation"
    CLOSE_EVALUATION = "close_evaluation"
    COMPLETED = "completed"
