from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from redis import ConnectionPool, Redis
from app.config import settings


@lru_cache()
def get_redis_pool():
    if settings.ENVIRONMENT == "testing":
        return None

    return ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=1,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
    )


def get_redis_client():
    if settings.ENVIRONMENT == "testing":
        import fakeredis

        redis_client = fakeredis.FakeStrictRedis()
    else:
        pool = get_redis_pool()
        redis_client = Redis(connection_pool=pool)
    return redis_client


RedisDependency = Annotated[Redis, Depends(get_redis_client)]
