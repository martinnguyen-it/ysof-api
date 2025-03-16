from app.domain.shared.entity import BaseEntity

from typing import Literal


class DailyBibleResponse(BaseEntity):
    gospel_ref: str
    epitomize_text: str

    season: Literal["Mùa Vọng", "Mùa Giáng Sinh", "Mùa Thường Niên", "Mùa Chay", "Mùa Phục Sinh"]
