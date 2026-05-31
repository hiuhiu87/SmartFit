#!/usr/bin/env bash

set -euo pipefail

MESSAGE="${1:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

print_help() {
  cat <<'EOF'
Usage:
  ./run-migration.sh "init schema"

What it does:
  1. Ensures .venv exists
  2. Runs alembic revision --autogenerate -m "<message>"
  3. Runs alembic upgrade head
EOF
}

if [[ -z "${MESSAGE}" ]]; then
  echo "Migration message is required." >&2
  print_help
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "Missing .venv. Run 'uv sync' or create the virtual environment first." >&2
  exit 1
fi

echo "Creating Alembic revision with message: ${MESSAGE}"
.venv/bin/alembic revision --autogenerate -m "${MESSAGE}"

echo "Applying latest migration"
.venv/bin/alembic upgrade head

echo "Migration flow completed"
