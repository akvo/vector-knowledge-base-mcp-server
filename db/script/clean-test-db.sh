#!/usr/bin/env bash
#shellcheck disable=SC2039

set -euo pipefail

psql --user akvo --no-align --list | \
    awk -F'|' '/^test/ {print $1}' | \
    while read -r dbname
    do
	psql --user akvo --dbname kb_mcp -c "DROP DATABASE ${dbname}"
    done

echo "Done"
