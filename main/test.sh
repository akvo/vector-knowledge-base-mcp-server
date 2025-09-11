#!/usr/bin/env bash

set -euo pipefail

MODE=${1:-all}

echo "Running tests in mode: $MODE"

case "$MODE" in
    integration)
        pytest \
            --asyncio-mode=auto \
            --maxfail=1 \
            --disable-warnings \
            -q \
            -m "not e2e" \
            --cov=app \
            --cov-report=term-missing \
            --cov-report=xml:coverage.xml \
            tests/
        ;;
    e2e)
        pytest \
            --asyncio-mode=auto \
            --maxfail=1 \
            --disable-warnings \
            -q \
            -m "e2e" \
            tests/
        ;;
    all|*)
        pytest \
            --asyncio-mode=auto \
            --maxfail=1 \
            --disable-warnings \
            -q \
            --cov=app \
            --cov-report=term-missing \
            --cov-report=xml:coverage.xml \
            tests/
        ;;
esac