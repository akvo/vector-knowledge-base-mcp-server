#!/usr/bin/env bash

set -euo pipefail

echo "Running tests with coverage..."

pytest \
--asyncio-mode=auto \
--maxfail=1 \
--disable-warnings \
-q \
--cov=app \
--cov-report=term-missing \
--cov-report=xml:coverage.xml \
tests/