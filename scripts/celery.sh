# Run worker and beat
# celery -A celery_worker.worker worker -B --loglevel=INFO


celery -A celery_worker.worker worker --loglevel=INFO

celery -A celery_worker.worker beat --loglevel=INFO
