FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends     build-essential curl netcat-traditional &&     rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

COPY . /app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Collect static using the correct manage.py path
RUN python config/manage.py collectstatic --noinput || true

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
# Prefer Gunicorn for production-ish runs:
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]

