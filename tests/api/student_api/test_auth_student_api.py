import unittest
from mongoengine import connect, disconnect
from fastapi.testclient import TestClient
from app.main import app
import mongomock
from app.infra.security.security_service import get_password_hash, verify_password
from app.models.student import StudentModel, SeasonInfo
from app.models.reset_otp import ResetOTPModel
from unittest.mock import patch
from app.domain.auth.entity import TokenData
import pytest
from datetime import datetime, timezone, timedelta


class TestAuthStudentApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        disconnect()
        connect(
            "mongoenginetest",
            host="mongodb://localhost:1234",
            mongo_client_class=mongomock.MongoClient,
        )
        cls.client = TestClient(app)
        cls.user: StudentModel = StudentModel(
            status="active",
            seasons_info=[SeasonInfo(numerical_order=1, group=1, season=3)],
            email="student@example.com",
            holy_name="Student",
            full_name="Student User",
            password=get_password_hash(password="local@local"),
        ).save()
        cls.inactive_student: StudentModel = StudentModel(
            status="inactive",
            seasons_info=[SeasonInfo(numerical_order=2, group=1, season=3)],
            email="inactive@example.com",
            holy_name="Inactive",
            full_name="Inactive Student",
            password=get_password_hash(password="password"),
        ).save()

    @classmethod
    def tearDownClass(cls):
        disconnect()

    def setUp(self):
        # Clean up ResetOTP collection before each test
        ResetOTPModel.objects.delete()

    @pytest.mark.order(1)
    def test_student_login(self):
        r = self.client.post(
            "/api/v1/student/auth/login",
            data={"username": "student@example.com", "password": "local@local"},
        )
        assert r.status_code == 200
        assert r.json().get("access_token")

    @pytest.mark.order(2)
    def test_student_change_password(self):
        with patch("app.infra.security.security_service.verify_token") as mock_token:
            mock_token.return_value = TokenData(email=self.user.email)
            new_password = "new_password"

            r = self.client.put(
                "/api/v1/student/auth/change-password",
                json={"new_password": new_password, "old_password": "dummy"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )

            assert r.status_code == 400
            assert r.json().get("detail") == "Sai mật khẩu"

            r = self.client.put(
                "/api/v1/student/auth/change-password",
                json={"new_password": new_password, "old_password": "local@local"},
                headers={
                    "Authorization": "Bearer {}".format("xxx"),
                },
            )
            assert r.status_code == 200
            user: StudentModel = StudentModel.objects(id=self.user.id).get()
            assert verify_password(new_password, user.password)

    @pytest.mark.order(3)
    def test_student_forgot_password_success(self):
        with patch(
            "app.infra.tasks.email.send_email_forgot_password_otp_task.delay"
        ) as mock_send_email:
            r = self.client.post(
                "/api/v1/student/auth/forgot-password",
                json={"email": "student@example.com"},
            )
            assert r.status_code == 200
            assert r.json().get("message") == "Mã OTP đã được gửi đến email của bạn"
            mock_send_email.assert_called_once()

    @pytest.mark.order(4)
    def test_student_forgot_password_email_not_found(self):
        r = self.client.post(
            "/api/v1/student/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )
        assert r.status_code == 400
        assert r.json().get("detail") == "Email không tồn tại trong hệ thống"

    @pytest.mark.order(5)
    def test_student_forgot_password_inactive_account(self):
        r = self.client.post(
            "/api/v1/student/auth/forgot-password",
            json={"email": "inactive@example.com"},
        )
        assert r.status_code == 400
        assert r.json().get("detail") == "Tài khoản của bạn đã bị khóa"

    @pytest.mark.order(6)
    def test_student_verify_otp_success(self):
        # Create OTP for testing with timezone-aware datetime
        otp = "123456"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour from now
        ResetOTPModel(
            email="student@example.com",
            otp=otp,
            user_type="student",
            expires_at=expires_at,
            is_used=0,
        ).save()

        r = self.client.post(
            "/api/v1/student/auth/verify-otp",
            json={"email": "student@example.com", "otp": "123456"},
        )
        assert r.status_code == 200
        assert r.json().get("reset_token")

    @pytest.mark.order(7)
    def test_student_verify_otp_invalid_otp(self):
        # Create OTP for testing with timezone-aware datetime
        otp = "123456"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour from now
        ResetOTPModel(
            email="student@example.com",
            otp=otp,
            user_type="student",
            expires_at=expires_at,
            is_used=0,
        ).save()

        r = self.client.post(
            "/api/v1/student/auth/verify-otp",
            json={"email": "student@example.com", "otp": "654321"},
        )
        assert r.status_code == 400
        assert r.json().get("detail") == "Mã OTP không đúng"

    @pytest.mark.order(8)
    def test_student_verify_otp_not_found(self):
        r = self.client.post(
            "/api/v1/student/auth/verify-otp",
            json={"email": "student@example.com", "otp": "123456"},
        )
        assert r.status_code == 400
        assert r.json().get("detail") == "Không tìm thấy mã OTP. Vui lòng yêu cầu lại"

    @pytest.mark.order(9)
    def test_student_reset_password_success(self):
        # Create valid reset token
        with patch(
            "app.use_cases.student_endpoint.student_auth.reset_password.verify_reset_token"
        ) as mock_verify_token:
            mock_verify_token.return_value = TokenData(email="student@example.com", id="student")

            with patch(
                "app.infra.tasks.email.send_email_password_changed_task.delay"
            ) as mock_send_email:
                r = self.client.post(
                    "/api/v1/student/auth/reset-password",
                    json={"token": "valid_token", "new_password": "new_password123"},
                )
                assert r.status_code == 200
                assert r.json().get("message") == "Mật khẩu đã được thay đổi thành công"
                mock_send_email.assert_called_once()

    @pytest.mark.order(10)
    def test_student_reset_password_invalid_token(self):
        with patch(
            "app.use_cases.student_endpoint.student_auth.reset_password.verify_reset_token"
        ) as mock_verify_token:
            mock_verify_token.side_effect = Exception("Invalid token")

            r = self.client.post(
                "/api/v1/student/auth/reset-password",
                json={"token": "invalid_token", "new_password": "new_password123"},
            )
            assert r.status_code == 400
            assert r.json().get("detail") == "Token không hợp lệ hoặc đã hết hạn"
