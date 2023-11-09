#! /usr/bin/env bash
set -e

python ./app/backend_pre_start.py

celery -A app.celery.worker worker -E -l info -Q main-queue -c 1
