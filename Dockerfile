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
RUN python -m pip install -q -r requirements.txt

COPY . .


EXPOSE 8000
CMD [ "uvicorn", "app.main:app", "--host",  "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers"]
