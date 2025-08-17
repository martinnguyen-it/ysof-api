from static.email.entity import Template, TemplateContent

EMAIL_TEMPLATE: dict[Template, dict[TemplateContent, str]] = {
    Template.WELCOME: {
        TemplateContent.PLAIN_TEXT: """
        Xin chào {{full_name}},
        Chào mừng bạn đến với YSOF - Trường học Đức tin cho người trẻ.


        Đây là thông tin tài khoản của bạn:
        Email: {{email}}
        Mật khẩu: {{password}}


        Bạn truy cập trang web tại: {{url}}

        Thân mến,
        Admin Web YSOF
        """
    },
    Template.WELCOME_WITH_EXIST_ACCOUNT: {
        TemplateContent.PLAIN_TEXT: """
        Xin chào {{full_name}},
        Chào mừng bạn đến với YSOF - Trường học Đức tin cho người trẻ mùa {{season}}.


        Đây là thông tin tài khoản của bạn:
        Email: {{email}}
        Bạn vui lòng sử dụng mật khẩu mà bạn đã sử dụng ở mùa trước để đăng nhập.


        Bạn truy cập trang web tại: {{url}}

        Thân mến,
        Admin Web YSOF
        """
    },
    Template.FORGOT_PASSWORD_OTP: {
        TemplateContent.PLAIN_TEXT: """
        Xin chào {{full_name}},
        Bạn đã yêu cầu đặt lại mật khẩu cho tài khoản YSOF của mình.

        Mã OTP của bạn là: {{otp}}

        Mã này có hiệu lực trong 10 phút. Vui lòng không chia sẻ mã này với bất kỳ ai.

        Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.

        Thân mến,
        Admin Web YSOF
        """
    },
    Template.PASSWORD_CHANGED: {
        TemplateContent.PLAIN_TEXT: """
        Xin chào {{full_name}},
        Mật khẩu tài khoản YSOF của bạn đã được thay đổi thành công.

        Nếu bạn không thực hiện thay đổi này, vui lòng liên hệ với chúng tôi tại {{contact_email}}.

        Thân mến,
        Admin Web YSOF
        """
    },
}
