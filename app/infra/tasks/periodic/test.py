from datetime import datetime

from celery_config import celery_app


@celery_app.task
def test():
    print(">>print >> Test at", datetime.now())
    return f">> Test at {datetime.now()}"
