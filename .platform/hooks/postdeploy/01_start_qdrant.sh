#!/bin/bash
set -e

echo "Starting Qdrant container..."

docker compose -f docker-compose.yml pull
docker compose -f docker-compose.yml up -d

echo "Qdrant started."

docker ps