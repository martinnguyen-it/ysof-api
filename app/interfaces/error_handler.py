from app.infra.logging import get_logger

logger = get_logger()

# custom exception handler
# https://fastapi.tiangolo.com/tutorial/handling-errors/#install-custom-exception-handlers
class ApplicationLevelException(Exception):
    def __init__(self, msg: str):
        self.msg = msg
