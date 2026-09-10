#!/bin/bash
set -e

echo "Starting Qdrant..."

docker compose -f docker-compose.yml pull
docker compose -f docker-compose.yml up -d

echo "Running containers:"
docker ps