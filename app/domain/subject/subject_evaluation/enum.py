from app.shared.utils.general import ExtendedEnum


class QualityValueEnum(str, ExtendedEnum):
    STRONGLY_DISAGREE = "Hoàn toàn không đồng ý"
    DISAGREE = "Không đồng ý"
    NEUTRAL = "Trung lập"
    AGREE = "Đồng ý"
    STRONGLY_AGREE = "Hoàn toàn đồng ý"


class TypeQuestionEnum(str, ExtendedEnum):
    RADIO = "radio"
    CHECKBOX = "checkbox"
    TEXT = "text"
