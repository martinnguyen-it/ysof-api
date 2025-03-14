import requests
from app.domain.daily_bible.entity import DailyBibleResponse
from app.shared import response_object, use_case


class GetQuotesBibleUseCase(use_case.UseCase):
    def process_request(self):
        url = "https://ktcgkpv.org/readings/mass-reading"
        payload = "seldate="
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "text/plain",
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code == 200:
            resp = response.json()["data"]["mass_reading"][0]["gospel"][0]

            return DailyBibleResponse(epitomize_text=resp["INDEXING"], gospel_ref=resp["EPITOMIZE"])
        else:
            return response_object.ResponseFailure.build_not_found_error(message="Not found")
