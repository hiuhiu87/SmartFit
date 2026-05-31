# SmartFit Backend

Backend skeleton for SmartFit using FastAPI, SQLModel, PostgreSQL, Alembic, and Clean Architecture.

## Structure

- `app`: application bootstrap, settings, dependency wiring.
- `src/domain`: pure Python domain entities, enums, repository contracts, and domain services.
- `src/application`: use cases, commands, queries, and DTOs.
- `src/infrastructure`: SQLModel tables, repositories, database session, security, AI adapters.
- `src/presentation`: FastAPI routers, schemas, and exception handlers.
- `tests`: unit and integration tests.

## Run

### Quick start with script

There is a helper script at [run-backend.sh](/Users/hieunm37/Workspace/Project/smartfit/smartfit-backend/run-backend.sh:1).

Run backend from local source code and start PostgreSQL in Docker:

```bash
chmod +x run-backend.sh
./run-backend.sh source
```

Run backend from Docker image and start PostgreSQL in Docker:

```bash
chmod +x run-backend.sh
./run-backend.sh image
```

Force rebuild backend image before container run:

```bash
BUILD_IMAGE=1 ./run-backend.sh image
```

The script will:

- create `.env` from `.env.example` if missing
- create/start a PostgreSQL container named `smartfit-postgres`
- wait until PostgreSQL is healthy before continuing
- create a Docker network named `smartfit-local`
- run `alembic upgrade head` before starting the API
- run seed data after migrations
- use real Alembic revisions in normal flow
- in `source` mode: create `.venv`, install dependencies if needed, then run `uvicorn`
- in `image` mode: build or reuse `smartfit-backend:local`, then run the API container

Skip migrations or seed if needed:

```bash
RUN_MIGRATIONS=0 ./run-backend.sh source
RUN_MIGRATIONS=0 ./run-backend.sh image
RUN_SEED=0 ./run-backend.sh source
RUN_SEED=0 ./run-backend.sh image
```

Stop services:

```bash
docker stop smartfit-api smartfit-postgres
```

Remove services:

```bash
docker rm -f smartfit-api smartfit-postgres
```

Remove network:

```bash
docker network rm smartfit-local
```

### Quick start with Docker Compose

Use [compose.yaml](/Users/hieunm37/Workspace/Project/smartfit/smartfit-backend/compose.yaml:1) if you want PostgreSQL healthcheck, migration, seed, and backend startup managed together.

```bash
docker compose up --build
```

Run in background:

```bash
docker compose up -d --build
```

Stop compose stack:

```bash
docker compose down
```

Skip migration or seed in compose mode:

```bash
RUN_MIGRATIONS=0 docker compose up --build
RUN_SEED=0 docker compose up --build
```

### 1. Create venv

```bash
python3 -m venv .venv
source .venv/bin/activate
python -V
```

### 2. Install dependencies

Option A: with `uv`

```bash
uv sync
```

Option B: with `pip`

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

### 3. Configure environment

```bash
cp .env.example .env
```

Update `DATABASE_URL`, `JWT_SECRET_KEY`, and `OPENAI_API_KEY` as needed.

### 4. Run API

With activated venv:

```bash
uvicorn app.main:app --reload
```

Or with `uv`:

```bash
uv run uvicorn app.main:app --reload
```

Or use Docker image directly:

```bash
docker build -t smartfit-backend:local .
docker run --rm -p 8000:8000 --env-file .env smartfit-backend:local
```

### 5. Run tests

```bash
pytest
```

### 6. Run Alembic

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

Or use the helper script and pass only the message:

```bash
chmod +x run-migration.sh
./run-migration.sh "init schema"
```

Current repo state:

- an initial revision already exists in `alembic/versions`
- normal local startup should use `alembic upgrade head`
- `src/infrastructure/database/bootstrap.py` remains only as a development fallback if revisions are absent

### 7. Seed Exercises

Seed the exercise catalog manually:

```bash
python -m src.infrastructure.seed.seed_exercises
```

`run-backend.sh` and `docker compose up` already run seed automatically after migrations unless `RUN_SEED=0` is set.

### 8. Seed Mock Data

Seed mock data across all current tables:

```bash
chmod +x run-mock-data.sh
./run-mock-data.sh
```

This will create a mock user and related records for:

- user/profile/equipment/preferences/notification settings
- health summary and manual check-in
- readiness score
- exercises and exercise alternative
- workout plan, workout log, set logs, feedback
- AI request and chat message
- subscription
- analytics event

### 9. Postman Collection

Import the Postman collection at [postman/SmartFit-Backend.postman_collection.json](/Users/hieunm37/Workspace/Project/smartfit/smartfit-backend/postman/SmartFit-Backend.postman_collection.json:1).

Suggested order:

1. `Auth / Register`
2. `Auth / Login`
3. `Users / Update Profile`
4. `Users / Update Equipment`
5. `Users / Get Me`

Notes:

- collection variables `accessToken` and `refreshToken` are filled automatically after `Login` and `Refresh Token`
- default `baseUrl` is `http://127.0.0.1:8000`
- some requests are included for completeness but still hit stub or TODO endpoints

## Verification

Local skeleton check completed with:

```bash
.venv/bin/python -m compileall app src tests alembic
```

## Notes

- Domain entities are dataclasses and do not depend on FastAPI, SQLModel, or Pydantic.
- SQLModel table models are isolated in `src/infrastructure/database/models`.
- Router handlers are thin and delegate to use cases or explicit TODO placeholders.
- The readiness calculator and workout safety policy include executable domain logic with unit tests.
