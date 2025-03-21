import logging
import os
from logging.handlers import TimedRotatingFileHandler

from celery import Celery
from celery.signals import after_setup_logger, worker_process_init, worker_process_shutdown

from app.config import CeleryConfig, settings
from app.config.database import connect, disconnect

logger = logging.getLogger(__name__)

celery_config = CeleryConfig()

celery_app = Celery(
    "ysof_celery_worker",
    broker=f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASS}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}",
)

celery_app.config_from_object(celery_config)


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
