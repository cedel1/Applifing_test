FROM python:3.11-slim

WORKDIR /app

ENV C_FORCE_ROOT=1

COPY requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

WORKDIR /app

ENV PYTHONPATH=/app

COPY ./celery-worker-start.sh /worker-start.sh

RUN chmod +x /worker-start.sh

CMD ["bash", "/worker-start.sh"]
