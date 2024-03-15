"""Response object contain the actual results of the API calls"""

from typing import Any, Union

from app.shared import request_object


class ResponseSuccess:
    """
    Response success

    Args:
        value (str): The value of the response

    Attributes:
        value (Any): store value of the response
    """

    def __init__(self, value: Any = None):
        self.value = value

    def __nonzero__(self):
        return True

    __bool__ = __nonzero__


class ResponseFailure:
    """
    Response failure

    Args:
        type_ (str): The type of the response
        message (FailureMessage): The message of the response

    Attributes:
        type (str): store type of response
        message (str): store message of response
    """

    RESOURCE_ERROR = "ResourceError"
    PARAMETERS_ERROR = "ParametersError"
    SYSTEM_ERROR = "SystemError"
    AUTH_ERROR = "AuthError"
    RESOURCE_NOT_FOUND = "ResourceNotFound"

    def __init__(self, type_: str, message: "FailureMessage"):
        self.type = type_
        self.message = self._format_message(message)

    def _format_message(self, msg: "FailureMessage") -> str:
        """format error message

        :param msg: original message
        :return: str
        """

        if isinstance(msg, Exception):
            return "{}: {}".format(msg.__class__.__name__, "{}".format(msg))

        return msg

    @property
    def value(self):
        """return dictionary value of failure response

        :return: dict
        """

        return {"type": self.type, "message": self.message}

    def __nonzero__(self):
        return False

    __bool__ = __nonzero__

    @classmethod
    def build_resource_error(cls, message=None):
        return cls(cls.RESOURCE_ERROR, message)

    @classmethod
    def build_system_error(cls, message=None):
        return cls(cls.SYSTEM_ERROR, message)

    @classmethod
    def build_parameters_error(cls, message=None):
        return cls(cls.PARAMETERS_ERROR, message)

    @classmethod
    def build_auth_error(cls, message=None):
        return cls(cls.AUTH_ERROR, message)

    @classmethod
    def build_from_invalid_request_object(
        cls, invalid_request_object: request_object.InvalidRequestObject
    ) -> "ResponseFailure":
        """build response failure object from invalid request object

        :param invalid_request_object:
        :return: ResponseFailure
        """

        message = "\n".join(
            ["{}: {}".format(err["parameter"], err["message"]) for err in invalid_request_object.errors]
        )

        return cls.build_parameters_error(message)

    @classmethod
    def build_not_found_error(cls, message=None) -> "ResponseFailure":
        return cls(cls.RESOURCE_NOT_FOUND, message)


# Typing
FailureMessage = Union[Exception, str]
ResponseObject = Union[ResponseFailure, ResponseSuccess]
