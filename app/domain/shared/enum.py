from app.shared.utils.general import ExtendedEnum


class AccountStatus(str, ExtendedEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class AdminRole(str, ExtendedEnum):
    ADMIN = "admin"
    BDH = "bdh"
    BKT = "bkt"
    BTT = "btt"
    BKL = "bkl"
    BHV = "bhv"
    BHD = "bhd"


class Sort(str, ExtendedEnum):
    ASCE = "ascend"
    DESC = "descend"
