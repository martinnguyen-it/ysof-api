"""Database Module"""

from mongoengine import connect as mongo_engine_connect, disconnect_all

from app.config import settings


def connect() -> None:
    """
    Start database connection
    :return: None
    """
    print(settings.ENVIRONMENT)
    if settings.ENVIRONMENT == "testing" or settings.ENVIRONMENT == "local":
        return mongo_engine_connect(
            settings.MONGODB_DATABASE, host=settings.MONGODB_HOST, port=settings.MONGODB_PORT
        )
    else:
        config = dict(
            host=settings.MONGODB_HOST,
            port=settings.MONGODB_PORT,
        )
        if settings.MONGODB_USERNAME and settings.MONGODB_PASSWORD:
            config["username"] = settings.MONGODB_USERNAME
            config["password"] = settings.MONGODB_PASSWORD
            config["authentication_source"] = settings.MONGODB_DATABASE

        return mongo_engine_connect(
            settings.MONGODB_DATABASE,
            **config,
            alias="default",
        )


def disconnect() -> None:
    """
    Disconnect database
    :return:
    """
    disconnect_all()
