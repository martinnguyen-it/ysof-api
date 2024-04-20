from app.shared.utils.general import ExtendedEnum


class RolePermissionGoogleEnum(str, ExtendedEnum):
    ORGANIZER = "organizer"
    FILE_ORGANIZER = "fileOrganizer"
    WRITER = "writer"
    COMMENTER = "commenter"
    READER = "reader"
