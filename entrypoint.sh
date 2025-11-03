#!/bin/sh
set -e

cd /app

python config/manage.py migrate --noinput || true

exec "$@"
