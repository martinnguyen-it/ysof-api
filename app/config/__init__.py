import os
from pathlib import Path
from typing import ClassVar, List, Optional, Union

from celery.schedules import crontab
from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    # env variables
    LOG_LEVEL: str

    # mongodb
    MONGODB_HOST: str
    MONGODB_PORT: int
    MONGODB_DATABASE: str
    MONGODB_USERNAME: Optional[str] = None
    MONGODB_PASSWORD: Optional[str] = None
    MONGODB_EXPOSE_PORT: Optional[int] = None
    MONGO_CELERY_COLLECTION: str

    @field_validator("MONGODB_USERNAME", "MONGODB_PASSWORD", "MONGODB_EXPOSE_PORT", mode="before")
    def allow_none(cls, v):
        if v is None or v == "":
            return None
        else:
            return v

    # Security
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE: int = 1
    JWT_TOKEN_PREFIX: str

    UPLOAD_DIR: str = "/uploads"
    # project config
    PROJECT_NAME: str = "YSOF API"
    API_V1_STR: str = "/api/v1"
    API_PORT: Optional[int] = 8000

    BACKEND_CORS_ORIGINS: List[str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    ENVIRONMENT: str
    ROOT_DIR: ClassVar = Path(__file__).parent.parent.parent

    FOLDER_GCLOUD_ID: str
    FOLDER_GCLOUD_AVATAR_ID: str
    KEY_PATH_GCLOUD: str = "google-credentials/gcloud-service-credentials-staging.json"
    PREFIX_IMAGE_GCLOUD: str = "https://lh3.googleusercontent.com/d/"

    BREVO_API_KEY: str
    YSOF_EMAIL: str

    SMTP_MAIL_HOST: str
    SMTP_MAIL_PORT: str
    SMTP_MAIL_USER: str
    SMTP_MAIL_PASSWORD: str

    STUDENT_SUBJECT_EVALUATION_TEMPLATE: int
    STUDENT_NOTIFICATION_SUBJECT: int
    STUDENT_WELCOME_EMAIL_TEMPLATE: int
    STUDENT_FORGOT_PASSWORD_EMAIL_TEMPLATE: int
    STUDENT_REGISTER_EMAIL_TEMPLATE: int

    FE_ADMIN_BASE_URL: str
    FE_STUDENT_BASE_URL: str

    RABBITMQ_USER: str
    RABBITMQ_PASS: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int

    TIMEZONE: str

    REDIS_HOST: str
    REDIS_PASSWORD: str
    REDIS_PORT: str


class CeleryConfig(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    result_backend: str = "celery_config.celery_mongo_backend.CustomMongoBackend"
    mongodb_backend_settings: dict[str, Optional[str]] = {
        "host": os.getenv("MONGODB_HOST"),
        "port": os.getenv("MONGODB_PORT"),
        "database": os.getenv("MONGODB_DATABASE"),
        "taskmeta_collection": os.getenv("MONGO_CELERY_COLLECTION"),
        **(
            {
                "user": os.getenv("MONGODB_USERNAME"),
                "password": os.getenv("MONGODB_PASSWORD"),
                "authsource": os.getenv("MONGODB_DATABASE"),
            }
            if ["testing", "local"].count(os.getenv("ENVIRONMENT")) == 0
            and os.getenv("MONGODB_USERNAME")
            and os.getenv("MONGODB_PASSWORD")
            else {}
        ),
    }

    accept_content: list = ["pickle", "json"]
    task_serializer: str = "pickle"
    worker_prefetch_multiplier: int = 4

    # event_serializer = ['pickle']
    result_serializer: str = "json"

    C_FORCE_ROOT: bool = True
    # worker_hijack_root_logger = False
    task_always_eager: bool = False

    timezone: str = os.getenv("TIMEZONE")

    """
    REGISTER DISTRIBUTED TASKS HERE
    Ref: http://bit.ly/2xldMEC
    Gather celery tasks in others modules.
    Remeber audodiscover_task searches a list of packages for a "tasks.py" module.
    You have to list here all the task-module you have:
    """
    register_tasks: list = []

    """
    `include` is an important config that loads needed modules to the worker
    Don't delete rows, only add the new module here.
    See problem at https://stackoverflow.com/q/55998650/1235074
    """
    include: list = register_tasks + [
        "app",
        "app.infra.tasks.periodic.test",
        "app.infra.tasks.email",
        "app.infra.tasks.periodic.manage_form_absent",
        "app.infra.tasks.periodic.manage_form_evaluation",
        "app.infra.tasks.drive_file",
    ]

    """
    celery beat schedule tasks
    """
    beat_schedule: ClassVar = {
        "add-every-5-minute": {
            "task": "app.infra.tasks.periodic.test.test",
            "schedule": crontab(minute="*/5"),
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


# init settings instance
settings = Settings()
