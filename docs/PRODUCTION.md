# Production checklist

## Environment

- Set strong `JWT_SECRET_KEY` (32+ random bytes)
- `ALLOW_REGISTRATION=false`
- `EXPOSE_RESET_TOKEN=false`
- `COOKIE_SECURE=true` (HTTPS only)
- `COOKIE_SAMESITE=lax` or `strict`
- Configure real SMTP (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`)
- Set `SITE_URL`, `OIDC_ISSUER`, `OIDC_FRONTEND_BASE_URL` to public HTTPS URLs
- Change `INITIAL_ADMIN_PASSWORD` before first deploy
- Set `INITIAL_ADMIN_EMAIL` for password reset

## Site content

- `SITE_OWNER_NAME`, `SITE_TAGLINE`, `SITE_BIO`, `SITE_SKILLS`
- `SITE_GITHUB_URL`, `SITE_TELEGRAM`, `SITE_RESUME_URL`
- Fill portfolio projects in `/admin/projects` (mark featured)

## Frontend

- `NUXT_PUBLIC_SITE_NAME`, `NUXT_PUBLIC_OWNER_NAME`, `NUXT_PUBLIC_TAGLINE`
- `NUXT_PUBLIC_SITE_URL=https://your-domain`

## Security

- Do not commit `.env`
- Rotate OIDC client secrets in production
- Review CORS_ORIGINS (exact origins only)
- Rate limit: `AUTH_RATE_LIMIT_PER_MINUTE`

## Monitoring

- Docker healthchecks on backend (`GET /`)
- External uptime ping to `https://your-domain/` and `/api/v1/site/status`
- Watch container logs: `docker compose logs -f backend`

## Backup

- Backup PostgreSQL volume regularly
