from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "ysof_celery_worker",
    broker=f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASS}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}",
    include=["app.infra.tasks.periodic.test"],
)
celery_app.conf.timezone = settings.CELERY_TIMEZONE

celery_app.conf.beat_schedule = {
    "add-every-2-minute": {"task": "app.infra.tasks.periodic.test.test", "schedule": crontab(minute="*/2")},
}
