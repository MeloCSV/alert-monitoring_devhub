#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$SCRIPT_DIR/alert-monitoring-back-web-api/alert_monitoring/api/boot/docker"

cd "$DOCKER_DIR"
docker compose up -d
