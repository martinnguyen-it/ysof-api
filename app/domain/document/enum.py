from app.shared.utils.general import ExtendedEnum


class DocumentType(str, ExtendedEnum):
    """_summary_

    Args:
        annual: For seasons can access /
        common: Just only each admin in current season can access /
        internal: Just only each admin in current season and belong same department can access /
        student: Document for student
    """

    ANNUAL = "annual"
    COMMON = "common"
    INTERNAL = "internal"
    STUDENT = "student"


class GoogleFileType(str, ExtendedEnum):
    SPREAD_SHEET = "spread_sheet"
    DOCUMENT = "document"
