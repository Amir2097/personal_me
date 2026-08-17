# Цифровое Сукно — production checklist

Standalone-стек: `docker compose -f docker-compose.billiards.yml up --build -d`

Публичная точка входа — nginx на `:8080` (`nginx/sukno.conf`). API напрямую — `:8010`.

## Перед первым деплоем

1. Скопируйте `apps/billiards-api/.env.example` в `.env` (или задайте переменные в compose/оркестраторе).
2. Сгенерируйте `JWT_SECRET_KEY` (32+ случайных байт).
3. Смените `INITIAL_ADMIN_PASSWORD` и задайте реальный `INITIAL_ADMIN_EMAIL`.
4. Установите `ALLOW_LEGACY_ADMIN_KEY=false` и очистите `SUKNO_ADMIN_KEY`.
5. Настройте SMTP — без него сброс пароля и верификация email не работают в prod.
6. Задайте `FRONTEND_BASE_URL` и `CORS_ORIGINS` на ваш HTTPS-домен (точное совпадение origin).
7. `COOKIE_SECURE=true` при работе только по HTTPS.

## Регистрация и роли

| Настройка | Рекомендация prod |
|-----------|-------------------|
| `ALLOW_REGISTRATION` | `false` — аккаунты создаёт admin |
| `REQUIRE_EMAIL_VERIFICATION` | `true` |
| `EXPOSE_RESET_TOKEN` / `EXPOSE_VERIFICATION_TOKEN` | `false` |

Роли: **player** → **operator** → **admin**. Назначение — в `/admin/users`.

## Права на табло и синхронизацию

| Действие | Кто может |
|----------|-----------|
| Просмотр табло по ссылке `/tv?room=КОД` | Все, без входа |
| Создание комнаты, push состояния, закрытие | **operator** / **admin** |
| Пара вносит счёт своего матча | **player** с привязанным логином (claim / setup) |
| История партий / академия / профиль | Владелец аккаунта (player+) |

Код комнаты — **8 символов** (без O/0/I/1/L). TTL по умолчанию **12 часов** (продлевается при каждом push; `SYNC_ROOM_TTL_HOURS=0` отключает автоистечение).

Гибрид турнира: пара с привязанным аккаунтом пишет счёт в живую комнату (`POST /cup/sessions/{code}/events`); табло обновляется сразу. Оператор на пульте может перебить. Device/гость — только просмотр.

## Миграции БД

API при старте выполняет `alembic upgrade head` (`app/core/migrations.py`).

Ручной прогон из каталога `apps/billiards-api`:

```bash
alembic upgrade head
```

При обновлении с версии без Alembic baseline `001_sukno_baseline` создаст недостающие таблицы (`checkfirst`), не трогая существующие.

## UI (Dockerfile.prod)

Сборка с `NUXT_APP_BASE_URL=/` для корня домена. Runtime:

- `NUXT_PUBLIC_API_BASE_URL=""` — same-origin `/api` через nginx
- `NUXT_PUBLIC_HUB_URL=""` — без hub SSO

## Мониторинг и бэкапы

- Health: `GET /` на API, healthcheck в compose
- OpenAPI: `/api/sukno/docs`
- Бэкап volume PostgreSQL (`sukno_postgres_data`) и `sukno_uploads_data` (аватары)
- Логи: `docker compose -f docker-compose.billiards.yml logs -f billiards-api`

## Dev vs prod

| | Dev compose | Prod |
|---|-------------|------|
| `ALLOW_LEGACY_ADMIN_KEY` | `true` | `false` |
| `EXPOSE_*_TOKEN` | можно `true` + Mailpit | `false` |
| Mailpit | `:8026` UI | реальный SMTP |

Локально: admin / admin123 (если не меняли), legacy key `sukno-dev-admin` только при `ALLOW_LEGACY_ADMIN_KEY=true`.

## Связь с hub (DAUTOVTECH)

Полный monorepo hub использует общую Postgres; таблицы Sukno в hub Alembic помечены как `SUKNO_OWNED_TABLES` и не удаляются hub-миграциями. Standalone Sukno ведёт свои миграции в `apps/billiards-api/alembic/`.
