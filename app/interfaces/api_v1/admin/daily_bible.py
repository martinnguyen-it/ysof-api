from fastapi import APIRouter, Depends

from app.domain.daily_bible.entity import DailyBibleResponse
from app.infra.security.security_service import get_current_admin
from app.shared.decorator import response_decorator
from app.use_cases.daily_bible.get_quotes_bible import GetQuotesBibleUseCase


router = APIRouter()


@router.get(
    "/daily-quotes", dependencies=[Depends(get_current_admin)], response_model=DailyBibleResponse
)
@response_decorator()
def get_daily_quotes(
    get_quotes_bible_use_case: GetQuotesBibleUseCase = Depends(GetQuotesBibleUseCase),
):
    return get_quotes_bible_use_case.process_request()
