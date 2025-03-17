import json
import re
import requests
from app.config.redis import RedisDependency
from app.domain.daily_bible.entity import DailyBibleResponse
from app.shared import response_object, use_case
from app.shared.utils.general import get_ttl_until_midnight

URL = "https://ktcgkpv.org/readings/mass-reading"
HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "text/plain",
}
PAYLOAD = "seldate="


class GetQuotesBibleUseCase(use_case.UseCase):
    def __init__(self, redis_client: RedisDependency):
        self.redis_client = redis_client

    def process_request(self):
        if not self.redis_client.exists("daily-bible-quotes"):
            try:
                response = self._fetch_data()
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
        return DailyBibleResponse(**json.loads(self.redis_client.get("daily-bible-quotes")))

    def _fetch_data(self):
        return requests.post(URL, headers=HEADERS, data=PAYLOAD)

    def _cache_response(self, data):
        resp = data["data"]["mass_reading"][0]
        season = self._extract_season(resp["date_info"]["daily_title"])
        cache_data = json.dumps(
            DailyBibleResponse(
                epitomize_text=resp["gospel"][0]["INDEXING"],
                gospel_ref=resp["gospel"][0]["EPITOMIZE"],
                season=season,
            ).model_dump(),
            default=str,
        )
        ttl = get_ttl_until_midnight()
        self.redis_client.setex("daily-bible-quotes", ttl, cache_data)

    def _extract_season(self, daily_title):
        pattern = r"Mùa [A-ZÀ-Ỹa-zà-ỹ ]+"
        match = re.search(pattern, daily_title)
        return match.group() if match else "Unknown Season"
