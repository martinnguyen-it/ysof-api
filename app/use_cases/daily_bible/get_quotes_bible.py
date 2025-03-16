import json
import re
from cachetools import TTLCache
import requests
from app.domain.daily_bible.entity import DailyBibleResponse
from app.shared import response_object, use_case
from app.shared.utils.general import get_ttl_until_midnight

cache = TTLCache(maxsize=10, ttl=get_ttl_until_midnight())

URL = "https://ktcgkpv.org/readings/mass-reading"
HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "text/plain",
}
PAYLOAD = "seldate="


class GetQuotesBibleUseCase(use_case.UseCase):
    def process_request(self):
        if "daily-bible-quotes" not in cache:
            try:
                response = self._fetch_data()
                print("None cache ⬇️⬇️")
                if response.status_code == 200:
                    self._cache_response(response.json())
                else:
                    return response_object.ResponseFailure.build_not_found_error(
                        message="Not found"
                    )
            except requests.RequestException as e:
                return response_object.ResponseFailure.build_system_error(message=str(e))
            except (KeyError, ValueError):
                return response_object.ResponseFailure.build_system_error(
                    message="Invalid response format"
                )
        return DailyBibleResponse(**json.loads(cache["daily-bible-quotes"]))

    def _fetch_data(self):
        return requests.post(URL, headers=HEADERS, data=PAYLOAD)

    def _cache_response(self, data):
        resp = data["data"]["mass_reading"][0]
        season = self._extract_season(resp["date_info"]["daily_title"])
        cache["daily-bible-quotes"] = json.dumps(
            DailyBibleResponse(
                epitomize_text=resp["gospel"][0]["INDEXING"],
                gospel_ref=resp["gospel"][0]["EPITOMIZE"],
                season=season,
            ).model_dump(),
            default=str,
        )

    def _extract_season(self, daily_title):
        pattern = r"Mùa [A-ZÀ-Ỹa-zà-ỹ ]+"
        match = re.search(pattern, daily_title)
        return match.group() if match else "Unknown Season"
