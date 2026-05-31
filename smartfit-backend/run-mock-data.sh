#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [[ ! -x .venv/bin/python ]]; then
  echo "Missing .venv. Run 'uv sync' first." >&2
  exit 1
fi

echo "Running mock data seed for all tables"
.venv/bin/python -m src.infrastructure.seed.seed_mock_data
echo "Mock data seed finished"
