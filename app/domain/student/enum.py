from app.shared.utils.general import ExtendedEnum


class SexEnum(str, ExtendedEnum):
    MALE = "Nam"
    FEMALE = "Nữ"


class FieldStudentEnum(str, ExtendedEnum):
    numerical_order = "MSHV"
    group = "Nhóm"
    holy_name = "Tên thánh"
    full_name = "Họ và tên"
    sex = "Giới tính"
    date_of_birth = "Ngày sinh"
    origin_address = "Quê quán"
    diocese = "Giáo phận bạn đang sinh hoạt"
    phone_number = "Số điện thoại"

    email = "Email"
    password = "Mật khẩu"
    avatar = "Ảnh đại diện"

    education = "Trình độ học vấn"
    job = "Nghề nghiệp"

    note = "Ghi chú"
