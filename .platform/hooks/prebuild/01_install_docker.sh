#!/bin/bash
set -e

echo "Installing Docker..."

if ! command -v docker >/dev/null 2>&1; then
    dnf install -y docker
fi

systemctl enable docker
systemctl start docker

if id "webapp" >/dev/null 2>&1; then
    usermod -aG docker webapp
fi

docker --version