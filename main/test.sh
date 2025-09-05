#!/usr/bin/env bash

set -euo pipefail

echo "Running tests"
/usr/local/bin/pytest -vvv -rP
