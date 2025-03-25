from app.domain.daily_bible.enum import LiturgicalSeason
from app.domain.shared.entity import BaseEntity


class DailyBibleResponse(BaseEntity):
    gospel_ref: str
    epitomize_text: str

    season: LiturgicalSeason
