import json
import logging
import re
import requests
from app.config.redis import RedisDependency
from app.domain.daily_bible.entity import DailyBibleResponse
from app.domain.daily_bible.enum import LiturgicalSeason
from app.shared import response_object, use_case
from app.shared.utils.general import get_ttl_until_midnight

logger = logging.getLogger(__name__)

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

        season_key = resp["date_info"]["season"]
        season_value = LiturgicalSeason[season_key].value  # Map key to value

        try:
            cache_data = json.dumps(
                DailyBibleResponse(
                    epitomize_text=resp["gospel"][0]["INDEXING"],
                    gospel_ref=resp["gospel"][0]["EPITOMIZE"],
                    season=season_value,
                ).model_dump(),
                default=str,
            )
        except IndexError as e:
            if "special_content" in resp:
                # Regex patterns, split to comply with line length < 100
                epitomize_pattern = (
                    r'<div class="gospel reading division">.*?'
                    r'<div class="division-header"><span>Tin Mừng</span></div>.*?'
                    r'<p class="gospel\[epitomize\] epitomize">([^<]+)</p>'
                )
                reference_pattern = (
                    r'<div class="gospel reading division">.*?'
                    r'<div class="division-header"><span>Tin Mừng</span></div>.*?'
                    r'<div class="gospel\[indexing\] right-indexing sel-transparent dropdown">.*?'
                    r'<span class="btn dropdown-toggle" data-toggle="dropdown">([^<]+)\s*'
                    r'<i class="fa fa-caret-down"[^>]*></i></span>'
                )
                epitomize_match = re.search(epitomize_pattern, resp["special_content"], re.DOTALL)
                epitomize_text = (
                    epitomize_match.group(1).strip().strip("&nbsp;") if epitomize_match else None
                )

                # Find reference text
                reference_match = re.search(reference_pattern, resp["special_content"], re.DOTALL)
                reference_text = (
                    reference_match.group(1).strip().strip("&nbsp;") if reference_match else None
                )
                cache_data = json.dumps(
                    DailyBibleResponse(
                        epitomize_text=reference_text,
                        gospel_ref=epitomize_text,
                        season=season_value,
                    ).model_dump(),
                    default=str,
                )
            else:
                raise (e)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return response_object.ResponseFailure.build_system_error(message=str(e))
        ttl = get_ttl_until_midnight()
        self.redis_client.setex("daily-bible-quotes", ttl, cache_data)
