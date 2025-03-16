import unittest
from unittest.mock import patch
import responses
from fastapi.testclient import TestClient
import mongomock
from mongoengine import connect, disconnect
from app.domain.auth.entity import TokenData
from app.infra.security.security_service import get_password_hash
from app.main import app
from app.models.student import SeasonInfo, StudentModel

mock_response_value_bible = {
    "data": {
        "mass_reading": [
            {
                "display_text": "Ngày thường",
                "date_info": {"season": "EAS", "daily_title": "Thứ Tư Tuần II - Mùa Chay"},
                "gospel": [
                    {
                        "INDEXING": "Mt 5,20-26",
                        "EPITOMIZE": "Hãy đi làm hoà với người anh em ấy đã.",
                        "LEAD": '<span class="holycross">&#x2720;</span>Tin Mừng Chúa Giê-su Ki-tô theo thánh Mát-thêu.',
                        "CONTENT": "<p><sup>20</sup> Khi ấy, Đức Giê-su nói với các môn đệ rằng : “Thầy bảo cho anh em biết, nếu anh em không ăn ở công chính hơn các kinh sư và người Pha-ri-sêu, thì sẽ chẳng được vào Nước Trời.</p><p><sup>21</sup> “Anh em đã nghe Luật dạy người xưa rằng : Chớ giết người ; ai giết người, thì đáng bị đưa ra toà. <sup>22</sup> Còn Thầy, Thầy bảo cho anh em biết : Ai giận anh em mình, thì đáng bị đưa ra toà. Ai mắng anh em mình là đồ ngốc, thì đáng bị đưa ra trước Thượng Hội Đồng. Còn ai chửi anh em mình là quân phản đạo, thì đáng bị lửa hoả ngục thiêu đốt. <sup>23</sup> Vậy, nếu khi anh sắp dâng lễ vật trước bàn thờ, mà sực nhớ có người anh em đang có chuyện bất bình với anh, <sup>24</sup> thì hãy để của lễ lại đó trước bàn thờ, đi làm hoà với người anh em ấy đã, rồi trở lại dâng lễ vật của mình. <sup>25</sup> Anh hãy mau mau dàn xếp với đối phương, khi còn đang trên đường đi với người ấy tới cửa công, kẻo người ấy nộp anh cho quan toà, quan toà lại giao anh cho thuộc hạ, và anh sẽ bị tống ngục. <sup>26</sup> Thầy bảo thật cho anh biết : anh sẽ không ra khỏi đó, trước khi trả hết đồng xu cuối cùng.”</p>",
                        "INDEXING_2": "Ed 18,31",
                        "CONTENT_2": "<p>Đức Chúa phán : Hãy quẳng khỏi các ngươi mọi tội phản nghịch các ngươi đã phạm. Hãy tạo cho mình một trái tim mới và một thần khí mới.</p>",
                    }
                ],
            }
        ],
    }
}


class TestDailyBibleApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect()
        connect(
            "mongoenginetest",
            host="mongodb://localhost:1234",
            mongo_client_class=mongomock.MongoClient,
        )
        cls.client = TestClient(app)
        cls.student: StudentModel = StudentModel(
            seasons_info=[
                SeasonInfo(
                    numerical_order=1,
                    group=2,
                    season=3,
                )
            ],
            status="active",
            holy_name="Martin",
            phone_number="0123456789",
            email="student@example.com",
            full_name="Nguyen Thanh Tam",
            password=get_password_hash(password="local@local"),
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    @responses.activate
    def test_get_daily_quotes(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.student.email)
            responses.add(
                responses.POST,
                "https://ktcgkpv.org/readings/mass-reading",
                json=mock_response_value_bible,
                status=200,
            )

            r = self.client.get(
                "/api/v1/student/daily-bible/daily-quotes",
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 200
            resp = r.json()
            assert resp["gospel_ref"] == "Hãy đi làm hoà với người anh em ấy đã."
            assert resp["epitomize_text"] == "Mt 5,20-26"
            assert resp["season"] == "Mùa Chay"


if __name__ == "__main__":
    unittest.main()
