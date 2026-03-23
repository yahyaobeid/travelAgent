#!/bin/bash
set -e

EC2_HOST="triphelix-ec2"
APP_DIR="~/triphelix"
IMAGE_NAME="triphelix"

echo "==> Building Docker image for linux/amd64..."
docker build --platform linux/amd64 -t $IMAGE_NAME .

echo "==> Transferring image to EC2 (this may take a minute)..."
docker save $IMAGE_NAME | ssh $EC2_HOST "docker load"

echo "==> Syncing docker-compose.prod.yaml to EC2..."
ssh $EC2_HOST "mkdir -p $APP_DIR"
scp docker-compose.prod.yaml $EC2_HOST:$APP_DIR/docker-compose.yaml

echo "==> Starting containers on EC2..."
ssh $EC2_HOST "cd $APP_DIR && docker compose up -d"

echo "==> Waiting for app to start..."
sleep 5

echo "==> Health check..."
for i in 1 2 3 4 5; do
  STATUS=$(ssh $EC2_HOST "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/" 2>/dev/null || echo "000")
  if [ "$STATUS" = "200" ] || [ "$STATUS" = "302" ]; then
    echo "    App is up (HTTP $STATUS)"
    echo "==> Done. Visit http://3.22.223.82:8000"
    exit 0
  fi
  echo "    Attempt $i: HTTP $STATUS — retrying in 5s..."
  sleep 5
done

echo "    Health check failed after 5 attempts. Check logs with:"
echo "    ssh $EC2_HOST 'docker compose -f ~/triphelix/docker-compose.yaml logs --tail=50'"
