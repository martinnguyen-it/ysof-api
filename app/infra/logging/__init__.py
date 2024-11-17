import logging
import sys
from pprint import pformat
import json
from loguru import logger
from loguru._defaults import LOGURU_FORMAT
from app.config import settings


class InterceptHandler(logging.Handler):
    loglevel_mapping = {
        50: "CRITICAL",
        40: "ERROR",
        30: "WARNING",
        20: "INFO",
        10: "DEBUG",
        0: "NOTSET",
    }

    """
    Default handler from examples in loguru documentation.
    See https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = self.loglevel_mapping[record.levelno]

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        log = logger.bind(request_id="app")
        log.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class CustomizeLogger:
    @classmethod
    def make_logger(cls):
        config = cls.load_logging_config()
        logging_config = config.get("logger")

        logger = cls.customize_logging(
            level=logging_config.get("level") if settings.ENVIRONMENT != "testing" else "debug",
            retention=logging_config.get("retention"),
            rotation=logging_config.get("rotation"),
            format=logging_config.get("format"),
        )
        return logger

    @classmethod
    def format_record(cls, record: dict) -> str:
        """
        Custom format for loguru loggers.
        Uses pformat for log any data like request/response body during debug.
        Works with logging if loguru handler it.

        Example:
        >>> payload = [{"users":[{"name": "Nick", "age": 87, "is_active": True},
        >>> {"name": "Alex", "age": 27, "is_active": True}], "count": 2}]
        >>> logger.bind(payload=).debug("users payload")
        >>> [   {   'count': 2,
        >>>         'users': [   {'age': 87, 'is_active': True, 'name': 'Nick'},
        >>>                      {'age': 27, 'is_active': True, 'name': 'Alex'}]}]
        """
        format_string = LOGURU_FORMAT

        if record["extra"].get("payload") is not None:
            record["extra"]["payload"] = pformat(
                record["extra"]["payload"], indent=4, compact=True, width=88
            )
            format_string += "\n<level>{extra[payload]}</level>"

        format_string += "{exception}\n"
        return format_string

    @classmethod
    def customize_logging(cls, level: str, rotation: str, retention: str, format: str):
        logger.remove()
        logger.add(
            sys.stdout,
            enqueue=True,
            backtrace=True,
            level=level.upper(),
            format=cls.format_record,
        )

        filename = f"api_{settings.ENVIRONMENT}.log"

        logger.add(
            "{dir}/logs/{filename}".format(dir=settings.ROOT_DIR, filename=filename),
            rotation=rotation,
            retention=retention,
            enqueue=True,
            backtrace=True,
            level=level.upper(),
            format=cls.format_record,
        )

        logging.basicConfig(handlers=[InterceptHandler()], level=0)
        logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
        for _log in ["uvicorn", "uvicorn.error", "fastapi"]:
            _logger = logging.getLogger(_log)
            _logger.handlers = [InterceptHandler()]

        return logger.bind(request_id=None, method=None)

    @classmethod
    def load_logging_config(cls):
        config = None

        config_path = "{}/logging_config.json".format(settings.ROOT_DIR)
        with open(config_path) as config_file:
            config = json.load(config_file)
        return config


def get_logger():
    logger = logging.getLogger(__name__)
    logger = CustomizeLogger.make_logger()
    return logger
