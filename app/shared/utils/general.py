from datetime import date, datetime
from enum import Enum
from typing import Optional, Union, Tuple
import calendar


class ExtendedEnum(Enum):
    """
    Extended python enum
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


def date2datetime(
    my_date: Union[date, datetime, str], min_time: bool = True, date_format: str = "%Y-%m-%d"
) -> Optional[datetime]:
    if not my_date:
        return None

    if isinstance(my_date, datetime):
        return my_date
    if isinstance(my_date, str):
        my_date = datetime.strptime(my_date, date_format)
    return datetime.combine(my_date, datetime.min.time() if min_time else datetime.max.time())


def last_day_of_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def get_quarter(quarter: int, year: int) -> Tuple[date, date]:
    first_month_of_quarter = 3 * quarter - 2
    last_month_of_quarter = 3 * quarter
    date_of_first_day_of_quarter = date(year, first_month_of_quarter, 1)
    date_of_last_day_of_quarter = date(year, last_month_of_quarter, calendar.monthrange(year, last_month_of_quarter)[1])
    return (date_of_first_day_of_quarter, date_of_last_day_of_quarter)


def get_month_list(dates):
    start, end = [datetime.strptime(_, "%Y-%m-%d") for _ in dates]
    total_months = lambda dt: dt.month + 12 * dt.year
    mlist = []
    for tot_m in range(total_months(start) - 1, total_months(end)):
        y, m = divmod(tot_m, 12)
        mlist.append(datetime(y, m + 1, start.day))
        # mlist.append(calendar.monthrange(y, m+1))
    return mlist
