from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings
from typing import ClassVar, List, Optional, Union
from pathlib import Path


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

    CURRENT_SEASON: int = 1

    FOLDER_GCLOUD_ID: str
    KEY_PATH_GCLOUD: str = "google-credentials/gcloud-service-credentials-staging.json"
    PREFIX_IMAGE_GCLOUD: str = "https://lh3.googleusercontent.com/d/"

    BREVO_API_KEY: str
    YSOF_EMAIL_SENDER: str

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


# init settings instance
settings = Settings()
