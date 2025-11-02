# Dev image with live reload & debug tooling
FROM python:3.12-slim

# system deps (build tools for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# Copy project
COPY . /app/

# Entrypoint for applying migrations before starting the server
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "config/manage.py", "runserver", "0.0.0.0:8000"]
