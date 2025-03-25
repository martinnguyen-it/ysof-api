from enum import Enum


class LiturgicalSeason(str, Enum):
    LNT = "Mùa Chay"
    CHR = "Mùa Giáng Sinh"
    ADV = "Mùa Vọng"
    EAS = "Mùa Phục Sinh"
    ORD = "Mùa Thường Niên"
