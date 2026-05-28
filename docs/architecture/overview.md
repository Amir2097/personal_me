# Architecture Overview

## Context

`personal_me` is a monorepo for a terminal-like personal developer portal.

## Runtime Topology

- `nginx` is the public entrypoint on port `80`.
- `frontend` (Nuxt 3 SSR) serves terminal UI on port `3000`.
- `backend` (FastAPI) serves API on port `8000`.
- `db` (PostgreSQL) stores relational data.

Traffic:

1. Browser -> `nginx`
2. `nginx` `/` -> `frontend`
3. `nginx` `/api/*` -> `backend`
4. `backend` -> `postgres`

## Auth and Command Flow

1. User runs `login <username> <password>` in the UI terminal.
2. Frontend calls `POST /api/v1/auth/login`.
3. Backend returns JWT bearer token.
4. Frontend stores token in Pinia store.
5. User runs command (for example `projects`).
6. Frontend calls `POST /api/v1/terminal/execute` with bearer token.
7. Backend validates token and executes command policy.

## Scalability Notes

- Add Redis for token revocation and command queueing.
- Split terminal command handlers by module with plugin registry.
- Add migration tooling (`alembic`) for database versioning.
