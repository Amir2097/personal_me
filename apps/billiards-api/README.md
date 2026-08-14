# Цифровое Сукно API

FastAPI-сервис колхоза, турнира, академии и табло. Хаб DAUTOVTECH больше не
обслуживает эти маршруты.

## Локально

```bash
cd apps/billiards-api
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8010
pytest
```

Таблицы создаются при старте (`SQLModel.create_all`). Пока используется та же
Postgres, что и хаб; схема клуба/тенантов не заводится.

## Auth

- Hub JWT с тем же `JWT_SECRET_KEY` принимается как есть (`sub` = username хаба).
- `POST /api/v1/billiards/auth/device` выдаёт локальный токен устройства
  (`sub=local_…`), без аккаунта хаба.
- GET комнат табло (`/sessions/{code}`) без авторизации.
- Админка: аккаунт с ролью `admin` (рекомендуется). Legacy-ключ `SUKNO_ADMIN_KEY` только при
  `ALLOW_LEGACY_ADMIN_KEY=true` (dev compose); на prod по умолчанию выключен.
  `POST /api/v1/site/admin/unlock` + JWT `typ=admin` — только в dev.
  Публичный `GET /api/v1/site/seo` без ключа.

## Маршруты

| Prefix | Назначение |
|---|---|
| `/api/v1/billiards/auth` | device token, `/me` |
| `/api/v1/kolkhoz` | комнаты и история колхоза |
| `/api/v1/cup` | комнаты и история турнира |
| `/api/v1/academy` | прогресс академии |
| `/api/v1/site` | публичное SEO + админ-настройки |
| `/api/sukno/docs` | OpenAPI |

В основном стеке nginx режет эти пути на этот сервис, остальной `/api/` — на хаб.
