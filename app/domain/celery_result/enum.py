from app.shared.utils.general import ExtendedEnum


class CeleryResultTag(str, ExtendedEnum):
    DEFAULT = "default"
    MANAGE_FORM_PERIODIC = "manage_form_periodic"
    MANAGE_FORM = "manage_form"
    SEND_MAIL = "send_mail"
    DRIVE_FILE = "drive_file"
