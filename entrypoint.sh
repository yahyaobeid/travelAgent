#!/bin/sh
set -e

python config/manage.py migrate --noinput

exec "$@"
