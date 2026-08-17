# Цифровое Сукно

The billiards app is **Цифровое Сукно** — a fixed brand, not a per-club
white-label. Clubs will later get internal tools (staff, tables, history) under
this same name. Do not add club rename or tenant slugs. Install SEO lives in
`billiards-api` (`sukno_site_settings`), not hub `site_settings`.

The hub is an optional identity provider. Play works without it. Cloud rooms
and snapshots talk to `apps/billiards-api`.

This file is the extraction map. Do not put Sukno game data into hub
`site_settings`.

## What stays in the hub

- Personal developer portal, terminal, projects, OIDC for *this* site
- Optional SSO: `go billiards` still mints a one-time code
- Auth routes `/api/v1/auth/*`

## What belongs to Цифровое Сукно

| Concern | Now | Next |
|---|---|---|
| Play, brackets, TV | Local, no login | Same |
| Brand | Fixed assets in `apps/billiards/public/brand/` | Same |
| SEO / site copy | `/admin/seo`, table `sukno_site_settings` | Same |
| Users | Sukno accounts (player/operator/admin), device JWT, optional hub SSO | Same |
| Sync rooms / history | `billiards-api`, 8-char codes, 12h TTL | PIN later |
| Pair self-score | Linked `player.username` + `/cup/sessions/{code}/events` | Same |
| Public site | Hub: `/billiards/`. Own domain: `NUXT_APP_BASE_URL=/` | Subdomain with `nginx/sukno.conf` |

`NUXT_APP_BASE_URL` switches the mount. On a real domain the home page is `/`,
not `/billiards/`. TV links and favicons follow that base.

## Auth

1. Sukno accounts: register/login, cookies, email verification, 2FA for operator+.
2. Device JWT for anonymous play (`POST /api/v1/billiards/auth/device`) — history/academy only; **not** sync rooms.
3. Optional hub SSO if `NUXT_PUBLIC_HUB_URL` is set.
4. TV `GET /sessions/{code}` stays public (kolkhoz and cup).
5. Sync write (create/push/close): **operator** or **admin** only.
6. Admin: Sukno account with role admin, or legacy `SUKNO_ADMIN_KEY` (dev only).

## Phases

1. **Done.** App opens without hub redirect. Hub login is a button, not a gate.
2. **Done.** Dedicated `billiards-api`. Device JWT. Brand fixed.
3. **Done.** Own-domain path (`baseURL=/`), brand mark/logo/favicon.
4. **Done.** Sukno accounts, RBAC, admin UI, Alembic, prod checklist.
5. **Club internals later.** Staff, tables, billing — not a second brand name.
6. **Install package.** Compose with UI + API + postgres. No hub frontend.
   Env: domain, SMTP, JWT secret. Still «Цифровое Сукно».
   Done for local/prod-shaped preview: `docker-compose.billiards.yml` +
   `apps/billiards/Dockerfile.prod`.

Do not split the git repo before a second real install exists.

Hub backend no longer owns Sukno models/services. Historical Alembic
revisions `013`–`016` stay; `alembic/env.py` ignores Sukno tables so
autogenerate cannot drop them from the shared DB.

## Standalone (prod images)

```bash
docker compose -f docker-compose.billiards.yml up --build
```

UI at `http://localhost:8080/` (nginx) or `:3010/`, API at `http://localhost:8010`.
