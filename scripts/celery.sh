# Run worker and beat
# celery -A celery_worker worker -B --loglevel=INFO


celery -A celery_worker worker --loglevel=INFO

celery -A celery_worker beat --loglevel=INFO
