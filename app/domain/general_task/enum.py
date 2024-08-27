from app.shared.utils.general import ExtendedEnum


class GeneralTaskType(str, ExtendedEnum):
    """_summary_

    Args:
        annual: For seasons can access /
        common: Just only each admin in current season can access /
        internal: Just only each admin in current season and belong same department can access
    """

    ANNUAL = "annual"
    COMMON = "common"
    INTERNAL = "internal"
