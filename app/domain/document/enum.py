from app.shared.utils.general import ExtendedEnum


class DocumentType(str, ExtendedEnum):
    """_summary_

    Args:
        annual: For sessions can access /
        common: Just only each admin in current session can access /
        internal: Just only each admin in current session and belong same department can access
    """
    ANNUAL = "annual"
    COMMON = "common"
    INTERNAL = "internal"
