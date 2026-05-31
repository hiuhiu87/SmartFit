#!/usr/bin/env bash

set -euo pipefail

FORCE_APPLY="${FORCE_APPLY:-0}"
RUN_UPGRADE="${RUN_UPGRADE:-0}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

print_help() {
  cat <<'EOF'
Usage:
  ./run-migration.sh create "init schema"
  ./run-migration.sh "init schema"
  RUN_UPGRADE=1 ./run-migration.sh "init schema"
  FORCE_APPLY=1 RUN_UPGRADE=1 ./run-migration.sh "init schema"
  ./run-migration.sh upgrade

Modes:
  create   Generate a new Alembic revision from model changes.
           This is the default mode when only a message is provided.
  upgrade  Apply existing unapplied revisions with alembic upgrade head.

Behavior for create mode:
  1. Ensures .venv exists
  2. Verifies database is already at current head before generating a new revision
  3. Runs alembic revision --autogenerate -m "<message>"
  4. Scans the generated file for risky patterns
  5. Does not auto-apply by default

Flags:
  RUN_UPGRADE=1  After create mode, also run alembic upgrade head
  FORCE_APPLY=1  Bypass risky-pattern guard when RUN_UPGRADE=1
EOF
}

ensure_venv() {
  if [[ ! -x .venv/bin/python ]]; then
    echo "Missing .venv. Run 'uv sync' or create the virtual environment first." >&2
    exit 1
  fi
}

normalize_revision_lines() {
  sed '/^[[:space:]]*$/d'
}

check_database_at_head() {
  local current_revisions
  local head_revisions

  current_revisions="$(.venv/bin/alembic current 2>/dev/null | awk '{print $1}' | normalize_revision_lines || true)"
  head_revisions="$(.venv/bin/alembic heads 2>/dev/null | awk '{print $1}' | normalize_revision_lines || true)"

  if [[ -z "${head_revisions}" ]]; then
    echo "Could not determine Alembic head revisions." >&2
    exit 1
  fi

  if [[ "${current_revisions}" != "${head_revisions}" ]]; then
    cat <<EOF >&2
Database is not at Alembic head.

Current revision(s):
${current_revisions:-<none>}

Head revision(s):
${head_revisions}

Apply existing migrations first:
  ./run-migration.sh upgrade
EOF
    exit 2
  fi
}

review_generated_revision() {
  local revision_file="$1"
  local risk_found=0
  local risky_patterns=(
    "op.add_column.*nullable=False"
    "op.alter_column.*nullable=False"
    "op.create_foreign_key"
    "op.drop_column"
    "op.drop_table"
    "op.drop_constraint"
  )

  echo "Reviewing generated migration for risky patterns"
  for pattern in "${risky_patterns[@]}"; do
    if grep -nE "${pattern}" "${revision_file}" >/tmp/smartfit_migration_risk_check.txt 2>/dev/null; then
      if [[ -s /tmp/smartfit_migration_risk_check.txt ]]; then
        risk_found=1
        echo "Found risky pattern: ${pattern}"
        cat /tmp/smartfit_migration_risk_check.txt
      fi
    fi
  done
  rm -f /tmp/smartfit_migration_risk_check.txt

  return "${risk_found}"
}

run_upgrade() {
  echo "Applying latest migration"
  .venv/bin/alembic upgrade head
  echo "Alembic upgrade completed"
}

create_revision() {
  local message="$1"
  local latest_before
  local latest_after
  local risk_found=0

  check_database_at_head

  latest_before="$(ls -1t alembic/versions/*.py 2>/dev/null | head -n 1 || true)"

  echo "Creating Alembic revision with message: ${message}"
  .venv/bin/alembic revision --autogenerate -m "${message}"

  latest_after="$(ls -1t alembic/versions/*.py | head -n 1)"

  if [[ "${latest_after}" == "${latest_before}" ]]; then
    echo "Could not detect a newly generated revision file." >&2
    exit 1
  fi

  echo "Generated revision: ${latest_after}"

  if review_generated_revision "${latest_after}"; then
    risk_found=0
  else
    risk_found=1
  fi

  if [[ "${RUN_UPGRADE}" != "1" ]]; then
    cat <<EOF
Revision generated successfully.

Next steps:
1. Review ${latest_after}
2. Apply it manually when ready:
   ./run-migration.sh upgrade

If you want one-shot generate + apply after review:
  RUN_UPGRADE=1 ./run-migration.sh "${message}"
EOF
    exit 0
  fi

  if [[ "${risk_found}" == "1" && "${FORCE_APPLY}" != "1" ]]; then
    cat <<EOF
Migration auto-apply has been blocked.

Reason:
- The generated revision contains risky patterns that often fail on databases with existing data.

What to do next:
1. Open ${latest_after}
2. Fix the migration manually
3. Run: ./run-migration.sh upgrade

If you have already reviewed the file and want to bypass this guard:
  FORCE_APPLY=1 RUN_UPGRADE=1 ./run-migration.sh "${message}"
EOF
    exit 2
  fi

  run_upgrade
}

ensure_venv

COMMAND="${1:-}"

if [[ -z "${COMMAND}" || "${COMMAND}" == "-h" || "${COMMAND}" == "--help" ]]; then
  print_help
  exit 0
fi

case "${COMMAND}" in
  create)
    MESSAGE="${2:-}"
    if [[ -z "${MESSAGE}" ]]; then
      echo "Migration message is required for create mode." >&2
      print_help
      exit 1
    fi
    create_revision "${MESSAGE}"
    ;;
  upgrade)
    run_upgrade
    ;;
  *)
    create_revision "${COMMAND}"
    ;;
esac
