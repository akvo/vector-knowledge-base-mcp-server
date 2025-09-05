#!/usr/bin/env bash
set -e

export COMPOSE_HTTP_TIMEOUT=180

docker compose \
  -f docker-compose.yml \
  -f docker-compose.override.yml \
  "$@"
