# Architecture Overview

## Context

**DAUTOVTECH** is a monorepo for a terminal-like personal developer portal (repository folder: `personal_me`).

## Runtime Topology

- `nginx` is the public entrypoint on port `80`.
- `frontend` (Nuxt 3 SSR) serves terminal UI on port `3000`.
- `billiards` (Nuxt) serves **Цифровое Сукно** under `/billiards/` on the hub (or `/` with `NUXT_APP_BASE_URL=/` on its own domain).
- `billiards-api` (FastAPI) serves kolkhoz/cup/academy on port `8010`.
- `backend` (FastAPI) serves hub API on port `8000`.
- `db` (PostgreSQL) stores relational data.

Traffic:

1. Browser -> `nginx`
2. `nginx` `/` -> `frontend`
3. `nginx` `/billiards/` -> `billiards`
4. `nginx` `/api/v1/{kolkhoz,cup,academy,billiards}` and `/api/sukno` -> `billiards-api`
5. `nginx` `/api/*` -> `backend`
6. `backend` / `billiards-api` -> `postgres`

## Auth and Command Flow

1. User runs `login <username> <password>` in the UI terminal.
2. Frontend calls `POST /api/v1/auth/login`.
3. Backend returns JWT bearer token.
4. Frontend stores token in Pinia store.
5. User runs command (for example `projects`).
6. Frontend calls `POST /api/v1/terminal/execute` with bearer token.
7. Backend validates token and executes command policy.

## Hobby / Billiards

- Billiards is **Цифровое Сукно** under `/billiards/` (see `docs/architecture/billiards-product.md`).
- Play, brackets and TV work without hub login. Device JWT talks to `billiards-api`.
- Hub SSO is optional cloud identity. Page `/hobby` can open the service as a guest or with SSO when already signed in.
- Integration key `billiards` still enables `go billiards` from the terminal.

## Scalability Notes

- Add Redis for token revocation and command queueing.
- Split terminal command handlers by module with plugin registry.
- Add migration tooling (`alembic`) for database versioning.
