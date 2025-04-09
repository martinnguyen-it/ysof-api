FROM python:3.10


WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y \
    curl \
    apt-transport-https \
    ca-certificates \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --upgrade pip
RUN pip install --upgrade pip pipenv wheel
RUN python -m pip install -q -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["celery", "-A", "celery_config.celery_worker",  "worker", "-B", "--loglevel=info" ]
