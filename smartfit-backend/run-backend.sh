#!/usr/bin/env bash

set -euo pipefail

MODE="${1:-source}"
BUILD_IMAGE="${BUILD_IMAGE:-0}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-1}"
RUN_SEED="${RUN_SEED:-1}"
DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-60}"

PROJECT_NAME="${PROJECT_NAME:-smartfit-backend}"
NETWORK_NAME="${NETWORK_NAME:-smartfit-local}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-smartfit-postgres}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-smartfit-api}"
BACKEND_IMAGE="${BACKEND_IMAGE:-smartfit-backend:local}"
POSTGRES_IMAGE="${POSTGRES_IMAGE:-postgres:16-alpine}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
APP_PORT="${APP_PORT:-8000}"
POSTGRES_DB="${POSTGRES_DB:-smartfit}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
DEFAULT_LOCAL_DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:${POSTGRES_PORT}/${POSTGRES_DB}"
DEFAULT_DOCKER_DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_CONTAINER}:5432/${POSTGRES_DB}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

print_help() {
  cat <<'EOF'
Usage:
  ./run-backend.sh source
  ./run-backend.sh image

Modes:
  source  Run PostgreSQL in Docker and FastAPI from local source/.venv
  image   Run PostgreSQL and FastAPI from Docker containers

Optional environment variables:
  BUILD_IMAGE=1          Build Docker image before running image mode
  RUN_MIGRATIONS=1       Run alembic upgrade head before starting backend
  RUN_SEED=1             Run seed data after migrations
  DB_WAIT_TIMEOUT=60     Seconds to wait for PostgreSQL health
  BACKEND_IMAGE=...      Override backend image tag
  APP_PORT=8000          Backend port exposed on host
  POSTGRES_PORT=5432     PostgreSQL port exposed on host
  POSTGRES_DB=smartfit
  POSTGRES_USER=postgres
  POSTGRES_PASSWORD=postgres
EOF
}

require_command() {
  local command_name="$1"
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Missing required command: ${command_name}" >&2
    exit 1
  fi
}

ensure_env_file() {
  if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "Created .env from .env.example"
  fi
}

ensure_network() {
  if ! docker network inspect "${NETWORK_NAME}" >/dev/null 2>&1; then
    docker network create "${NETWORK_NAME}" >/dev/null
    echo "Created Docker network ${NETWORK_NAME}"
  fi
}

ensure_postgres_container() {
  local running
  running="$(docker inspect -f '{{.State.Running}}' "${POSTGRES_CONTAINER}" 2>/dev/null || true)"

  if [[ "${running}" == "true" ]]; then
    echo "PostgreSQL container ${POSTGRES_CONTAINER} is already running"
    return
  fi

  if docker inspect "${POSTGRES_CONTAINER}" >/dev/null 2>&1; then
    docker start "${POSTGRES_CONTAINER}" >/dev/null
    echo "Started existing PostgreSQL container ${POSTGRES_CONTAINER}"
    return
  fi

  docker run -d \
    --name "${POSTGRES_CONTAINER}" \
    --network "${NETWORK_NAME}" \
    -e POSTGRES_DB="${POSTGRES_DB}" \
    -e POSTGRES_USER="${POSTGRES_USER}" \
    -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
    --health-cmd "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}" \
    --health-interval 5s \
    --health-timeout 5s \
    --health-retries 20 \
    --health-start-period 5s \
    -p "${POSTGRES_PORT}:5432" \
    "${POSTGRES_IMAGE}" >/dev/null

  echo "Started PostgreSQL container ${POSTGRES_CONTAINER}"
}

wait_for_postgres_ready() {
  local elapsed=0
  local status=""

  echo "Waiting for PostgreSQL to become ready"
  while (( elapsed < DB_WAIT_TIMEOUT )); do
    status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}unknown{{end}}' "${POSTGRES_CONTAINER}" 2>/dev/null || true)"

    if [[ "${status}" == "healthy" ]]; then
      echo "PostgreSQL is healthy"
      return
    fi

    if docker exec "${POSTGRES_CONTAINER}" pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; then
      echo "PostgreSQL responded to pg_isready"
      return
    fi

    sleep 2
    elapsed=$((elapsed + 2))
  done

  echo "Timed out waiting for PostgreSQL after ${DB_WAIT_TIMEOUT}s" >&2
  docker logs "${POSTGRES_CONTAINER}" || true
  exit 1
}

ensure_local_python_env() {
  if [[ ! -x .venv/bin/python ]]; then
    python3 -m venv .venv
    echo "Created local virtual environment at .venv"
  fi

  if [[ ! -x .venv/bin/uvicorn ]]; then
    echo "Installing project dependencies into .venv"
    .venv/bin/python -m pip install --upgrade pip
    .venv/bin/python -m pip install -e .
  fi
}

has_migration_revisions() {
  find alembic/versions -type f -name "*.py" ! -name "__init__.py" | grep -q .
}

run_schema_bootstrap_if_needed() {
  if has_migration_revisions; then
    return
  fi

  echo "No Alembic revision files found. Bootstrapping schema with SQLModel metadata."
  .venv/bin/python -m src.infrastructure.database.bootstrap
}

run_local_migrations() {
  if [[ "${RUN_MIGRATIONS}" != "1" ]]; then
    echo "Skipping migrations in source mode"
    return
  fi

  if ! has_migration_revisions; then
    run_schema_bootstrap_if_needed
    return
  fi

  echo "Running alembic migrations in source mode"
  .venv/bin/alembic upgrade head
}

run_local_seed() {
  if [[ "${RUN_SEED}" != "1" ]]; then
    echo "Skipping seed in source mode"
    return
  fi

  echo "Running seed data in source mode"
  .venv/bin/python -m src.infrastructure.seed.seed_exercises
}

run_source_mode() {
  require_command docker
  require_command python3
  ensure_env_file
  ensure_network
  ensure_postgres_container
  wait_for_postgres_ready
  ensure_local_python_env

  export DATABASE_URL="${DATABASE_URL:-${DEFAULT_LOCAL_DATABASE_URL}}"
  run_local_migrations
  run_local_seed

  echo "Running backend from source on http://127.0.0.1:${APP_PORT}"
  echo "Using DATABASE_URL=${DATABASE_URL}"
  exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}" --reload
}

build_backend_image() {
  docker build -t "${BACKEND_IMAGE}" .
}

run_image_mode() {
  require_command docker
  ensure_env_file
  ensure_network
  ensure_postgres_container
  wait_for_postgres_ready

  if [[ "${BUILD_IMAGE}" == "1" ]]; then
    build_backend_image
  elif ! docker image inspect "${BACKEND_IMAGE}" >/dev/null 2>&1; then
    echo "Docker image ${BACKEND_IMAGE} not found locally. Building it now."
    build_backend_image
  fi

  if docker inspect "${BACKEND_CONTAINER}" >/dev/null 2>&1; then
    docker rm -f "${BACKEND_CONTAINER}" >/dev/null
  fi

  echo "Running backend container ${BACKEND_CONTAINER} on http://127.0.0.1:${APP_PORT}"
  exec docker run --rm \
    --name "${BACKEND_CONTAINER}" \
    --network "${NETWORK_NAME}" \
    -p "${APP_PORT}:8000" \
    -e DATABASE_URL="${DEFAULT_DOCKER_DATABASE_URL}" \
    -e JWT_SECRET_KEY="${JWT_SECRET_KEY:-change-me}" \
    -e JWT_ALGORITHM="${JWT_ALGORITHM:-HS256}" \
    -e ACCESS_TOKEN_EXPIRE_MINUTES="${ACCESS_TOKEN_EXPIRE_MINUTES:-30}" \
    -e REFRESH_TOKEN_EXPIRE_DAYS="${REFRESH_TOKEN_EXPIRE_DAYS:-7}" \
    -e AI_PROVIDER="${AI_PROVIDER:-openrouter}" \
    -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
    -e OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}" \
    -e OPENROUTER_BASE_URL="${OPENROUTER_BASE_URL:-https://openrouter.ai/api/v1}" \
    -e OPENROUTER_MODEL="${OPENROUTER_MODEL:-openrouter/auto}" \
    -e OPENROUTER_TIMEOUT_SECONDS="${OPENROUTER_TIMEOUT_SECONDS:-20}" \
    -e OPENROUTER_MAX_OUTPUT_TOKENS="${OPENROUTER_MAX_OUTPUT_TOKENS:-2500}" \
    -e OPENROUTER_HTTP_REFERER="${OPENROUTER_HTTP_REFERER:-}" \
    -e OPENROUTER_APP_TITLE="${OPENROUTER_APP_TITLE:-SmartFit}" \
    -e ENVIRONMENT="${ENVIRONMENT:-local}" \
    -e RUN_MIGRATIONS="${RUN_MIGRATIONS}" \
    -e RUN_SEED="${RUN_SEED}" \
    "${BACKEND_IMAGE}" \
    sh -c 'if find alembic/versions -type f -name "*.py" ! -name "__init__.py" | grep -q .; then if [ "${RUN_MIGRATIONS}" = "1" ]; then alembic upgrade head; else echo "Skipping migrations in image mode"; fi; else echo "No Alembic revision files found. Bootstrapping schema with SQLModel metadata."; python -m src.infrastructure.database.bootstrap; fi && if [ "${RUN_SEED}" = "1" ]; then python -m src.infrastructure.seed.seed_exercises; else echo "Skipping seed in image mode"; fi && uvicorn app.main:app --host 0.0.0.0 --port 8000'
}

case "${MODE}" in
  source)
    run_source_mode
    ;;
  image)
    run_image_mode
    ;;
  help|-h|--help)
    print_help
    ;;
  *)
    echo "Unknown mode: ${MODE}" >&2
    print_help
    exit 1
    ;;
esac
