"""base use case class module"""
import traceback
from fastapi import HTTPException
from app.shared import response_object as res, request_object as req

from app.infra.logging import get_logger
from app.config import settings

logger = get_logger()

IS_PRODUCTION = settings.ENVIRONMENT == "production"


class UseCase:
    """
    Base use case class
    """

    def execute(self, request_object: req.RequestObject) -> res.ResponseObject:
        """execute use case

        return check request object valid and process request
        :param request_object:
        :return: Any
        """

        if not request_object:
            return res.ResponseFailure.build_from_invalid_request_object(request_object)
        try:
            result = self.process_request(request_object)
            # # default return success True
            # if not result:
            #     result = dict(
            #         success=True
            #     )

            # ensure return response success / failure object
            if not (result or isinstance(result, res.ResponseSuccess)):
                return result
            return res.ResponseSuccess(result)
        except Exception as exc:
            print(traceback.format_exc())
            if IS_PRODUCTION:
                logger.exception("Usecase error: {error}", error=exc, payload=exc)
            if isinstance(exc, HTTPException):
                raise exc

            return res.ResponseFailure.build_system_error("{}".format(exc))
            # return res.ResponseFailure.build_system_error(
            #     "{}: {}".format(exc.__class__.__name__, "{}".format(exc)))

    def process_request(self, request_object):
        """abstract process_request method"""
        raise NotImplementedError("process_request() not implemented by UseCase class")
