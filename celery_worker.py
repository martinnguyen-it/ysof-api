from celery import Celery
from celery.schedules import crontab
import logging
import os
from celery.signals import after_setup_logger
from logging.handlers import TimedRotatingFileHandler
from app.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "ysof_celery_worker",
    broker=f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASS}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}",
    include=["app", "app.infra.tasks.periodic.test", "app.infra.tasks.email"],
)
celery_app.conf.timezone = settings.CELERY_TIMEZONE
celery_app.conf.accept_content = ["pickle", "json"]
celery_app.conf.task_serializer = "pickle"

if not settings.ENVIRONMENT == "testing":
    celery_app.conf.worker_prefetch_multiplier = 4

celery_app.conf.beat_schedule = {
    "add-every-2-minute": {"task": "app.infra.tasks.periodic.test.test", "schedule": crontab(minute="*/2")},
}


@after_setup_logger.connect
def config_loggers(logger, *args, **kwags):
    logger = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(name)s : %(message)s")

    directory = os.getcwd()
    log_path = "{}/logs".format(directory)
    is_exist = os.path.exists(log_path)
    if not is_exist:
        os.makedirs(log_path)

    handler = TimedRotatingFileHandler(
        "{}/celery_{}.log".format(log_path, settings.ENVIRONMENT),
        when="W0",
        utc=True,
        backupCount=5,
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
