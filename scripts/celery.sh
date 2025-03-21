# Run worker and beat // Don't run on Windows
celery -A celery_config.celery_worker worker -B --loglevel=INFO


# On windows,run two commands below
# celery -A celery_config.celery_worker worker --loglevel=INFO
# celery -A celery_config.celery_worker beat --loglevel=INFO
