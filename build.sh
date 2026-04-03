#!/usr/bin/env bash
set -e

echo "Building React frontend..."
cd frontend && npm run build && cd ..

echo "Collecting static files..."
python config/manage.py collectstatic --noinput

echo "Build complete."
