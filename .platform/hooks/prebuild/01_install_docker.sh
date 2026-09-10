#!/bin/bash
set -e

echo "Installing Docker..."

if ! command -v docker >/dev/null 2>&1; then
    dnf install -y docker
fi

systemctl enable docker
systemctl start docker

echo "Installing Docker Compose..."

mkdir -p /usr/local/lib/docker/cli-plugins

curl -SL \
  https://github.com/docker/compose/releases/download/v5.5.0/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose

chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

echo "Docker version:"
docker --version

echo "Docker Compose version:"
docker compose version