"""Request object helpers"""

from typing import List, Union, Dict


class InvalidRequestObject:
    """
    Invalid request object

    Args:

    Attributes:
        errors (List[dict]): store list of errors,
    """

    def __init__(self):
        self.errors: List[dict] = []

    def add_error(self, parameter: str = "", message: str = "") -> None:
        """Add error to errors list

        :param parameter: Any
        :param message: Any
        :return: None
        """

        self.errors.append({"parameter": parameter, "message": message})

    def add_error_map(self, errors: Union[str, List, Dict]) -> None:
        """Add errors dictionary to erros list

        :param errors: errors collection
        :return: None
        """

        if isinstance(errors, str):
            self.add_error(message=errors)
        if isinstance(errors, list):
            for value in errors:
                self.add_error(message=value)
        if isinstance(errors, dict):
            for key, value in errors.items():
                self.add_error(parameter=key, message=value)

    def has_errors(self):
        """check if object has error

        :return: boolean
        """
        return len(self.errors) > 0

    def __nonzero__(self):
        return False

    __bool__ = __nonzero__


class ValidRequestObject:
    """
    Valid request object
    """

    @classmethod
    def builder(cls, adict):
        """abstract builder method"""
        raise NotImplementedError

    def __nonzero__(self):
        return True

    __bool__ = __nonzero__


# Typing
RequestObject = Union[ValidRequestObject, InvalidRequestObject]
