from enum import Enum


class TemplateContent(str, Enum):
    HTML = "html"
    PLAIN_TEXT = "plain_text"


class Template(str, Enum):
    WELCOME = "welcome"
