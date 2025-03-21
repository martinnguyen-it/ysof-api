import traceback
from functools import wraps

from celery.exceptions import Ignore

from app.domain.celery_result.enum import CeleryResultTag
from celery_config.celery_worker import celery_app, logger


def celery_app_with_error_handler(tag: CeleryResultTag = CeleryResultTag.DEFAULT):
    """
    A decorator to handle exceptions in Celery tasks.

    Args:
        tag (CeleryResultTag): Tag for categorizing the task (used in metadata).
    """

    def decorator(task_func):
        @celery_app.task(bind=True)
        @wraps(task_func)
        def wrapper(self, *args, **kwargs):
            try:
                return task_func(*args, **kwargs)
            except Exception as ex:
                logger.exception(ex)
                metadata = {
                    "tag": tag,
                    "name": str(self.name).rsplit(".", maxsplit=1)[-1],  # Task name
                    "description": str(ex),
                    "traceback": str(traceback.format_exc()),
                }

                self.update_state(state="FAILURE", meta=metadata, kwargs=kwargs)
                raise Ignore()

        return wrapper

    return decorator
