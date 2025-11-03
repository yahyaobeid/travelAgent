#!/bin/sh
set -e

cd /app

python config/manage.py migrate --noinput
python config/manage.py collectstatic --noinput

exec "$@"

