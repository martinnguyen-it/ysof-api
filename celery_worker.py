from celery import Celery
from celery.schedules import crontab
import logging
import os
from celery.signals import after_setup_logger, worker_process_init, worker_process_shutdown
from logging.handlers import TimedRotatingFileHandler
from app.config import settings
from app.config.database import connect, disconnect

logger = logging.getLogger(__name__)

celery_app = Celery(
    "ysof_celery_worker",
    broker=f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASS}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}",
    include=[
        "app",
        "app.infra.tasks.periodic.test",
        "app.infra.tasks.email",
        "app.infra.tasks.periodic.manage_form_absent",
        "app.infra.tasks.periodic.manage_form_evaluation",
    ],
)
celery_app.conf.timezone = settings.CELERY_TIMEZONE
celery_app.conf.accept_content = ["pickle", "json"]
celery_app.conf.task_serializer = "pickle"

if not settings.ENVIRONMENT == "testing":
    celery_app.conf.worker_prefetch_multiplier = 4

celery_app.conf.beat_schedule = {
    "add-every-2-minute": {
        "task": "app.infra.tasks.periodic.test.test",
        "schedule": crontab(minute="*/2"),
    },
    "check-open-form-absent-every-sunday": {
        "task": "app.infra.tasks.periodic.manage_form_absent.open_form_absent_task",
        "schedule": crontab(minute="00", hour=12, day_of_week=0, month_of_year="1-5,9-12"),
    },
    "check-close-form-absent-every-saturday": {
        "task": "app.infra.tasks.periodic.manage_form_absent.close_form_absent_task",
        "schedule": crontab(minute="00", hour=12, day_of_week=6, month_of_year="1-5,9-12"),
    },
    "check-close-form-evaluation-every-monday": {
        "task": "app.infra.tasks.periodic.manage_form_evaluation.close_form_evaluation_task",
        "schedule": crontab(minute="59", hour=23, day_of_week=1, month_of_year="1-5,9-12"),
    },
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


@worker_process_init.connect
def connect_db(**kwargs):
    connect()


@worker_process_shutdown.connect
def disconnect_db(**kwargs):
    disconnect()
