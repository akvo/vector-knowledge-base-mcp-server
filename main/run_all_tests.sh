#!/usr/bin/env bash

set -euo pipefail

echo "Running all tests: api, e2e, and mcp"

# 1. Integration tests
echo "=== FastAPI API Tests ==="
pytest \
    --asyncio-mode=auto \
    --maxfail=1 \
    --disable-warnings \
    -q \
    -m "not e2e and not mcp" \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=xml:coverage_integration.xml \
    tests/

# 2. E2E tests
echo "=== E2E Tests ==="
pytest \
    --asyncio-mode=auto \
    --maxfail=1 \
    --disable-warnings \
    -q \
    -m "e2e" \
    tests/

# 3. MCP tests
echo "=== MCP Tests ==="
pytest \
    --asyncio-mode=auto \
    --maxfail=1 \
    --disable-warnings \
    -q \
    -m "mcp" \
    tests/
