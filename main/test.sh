#!/usr/bin/env bash

set -euo pipefail

MODE=${1:-""}

if [[ -z "$MODE" ]]; then
    echo "❌ Please provide a test mode: api, e2e, mcp, or all"
    exit 1
fi

echo "Running tests in mode: $MODE"

# Common pytest args
PYTEST_BASE_ARGS=(
    --asyncio-mode=auto
    --maxfail=1
    --disable-warnings
    -q
    tests/
)

# Coverage args for api tests
COV_ARGS=(
    --cov=app
    --cov-report=term-missing
    --cov-report=xml:coverage.xml
)

# Function to run tests with a marker
run_tests() {
    local marker=$1
    local extra_args=("${@:2}")
    echo "=== Running $marker tests ==="
    pytest "${PYTEST_BASE_ARGS[@]}" -m "$marker" "${extra_args[@]}"
}

case "$MODE" in
    api)
        run_tests "not e2e and not mcp" "${COV_ARGS[@]}"
        ;;
    e2e)
        run_tests "e2e"
        ;;
    mcp)
        run_tests "mcp"
        ;;
    all)
        run_tests "not e2e and not mcp" "${COV_ARGS[@]}"
        run_tests "e2e"
        run_tests "mcp"
        ;;
    *)
        echo "❌ Unknown mode: $MODE. Allowed modes: api, e2e, mcp, all"
        exit 1
        ;;
esac
