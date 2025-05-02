from app.shared.utils.general import ExtendedEnum


class AbsentType(str, ExtendedEnum):
    NO_ATTEND = "no_attend"
    NO_EVALUATION = "no_evaluation"


class CreatedByEnum(str, ExtendedEnum):
    BTC = "BTC"
    HV = "HV"
