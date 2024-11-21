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
}
