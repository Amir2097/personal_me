# Personal Me: Terminal/IDE Developer Hub

Интерактивный личный портал разработчика в стиле терминала и IDE.  
Главная страница эмулирует CLI: пользователь вводит команды (`help`, `login`, `projects`, `clear`), получает ответы от FastAPI backend и после авторизации может работать с расширенными сервисами.

## Стек

- **Backend:** Python 3.11+, FastAPI, SQLModel, PostgreSQL, JWT.
- **Frontend:** Nuxt 3 (SSR), TypeScript, Tailwind CSS, Pinia.
- **DevOps:** Docker, Docker Compose, Nginx reverse proxy.

## Быстрый старт (Docker)

1. Убедитесь, что установлены Docker и Docker Compose.
2. В корне репозитория выполните:
   ```bash
   docker compose up --build
   ```
3. Откройте сервисы:
   - UI: `http://localhost`
   - Backend Swagger: `http://localhost/api/docs`
   - Backend OpenAPI: `http://localhost/api/openapi.json`

Остановка:

```bash
docker compose down
```

Сброс БД-тома:

```bash
docker compose down -v
```

## Структура репозитория

- `backend` — API, auth, обработка терминальных команд.
- `frontend` — Nuxt-приложение с терминальным UI.
- `docs` — техническая документация и архитектурные заметки.
- `nginx` — конфиг reverse proxy.
- `docker-compose.yml` — оркестрация окружения.

## Основные API эндпоинты

- `GET /` — healthcheck backend.
- `POST /api/v1/auth/login` — логин и выдача пары JWT (access + refresh).
- `POST /api/v1/auth/register` — регистрация нового пользователя + выдача JWT.
- `POST /api/v1/auth/refresh` — ротация пары токенов по refresh токену.
- `POST /api/v1/auth/logout` — отзыв refresh токена и logout.
- `POST /api/v1/auth/password-reset/request` — запрос токена сброса пароля.
- `POST /api/v1/auth/password-reset/confirm` — подтверждение сброса по токену.
- `POST /api/v1/auth/change-password` — смена пароля (требуется JWT).
- `GET /api/v1/auth/me` — профиль текущего пользователя (`username`, `is_admin`).
- `POST /api/v1/terminal/execute` — выполнение terminal-команды.
- `GET /api/v1/integrations` — список включённых интеграций.
- `GET /api/v1/integrations/all` — все интеграции (только admin).
- `POST /api/v1/integrations` — создать интеграцию (только admin).
- `PATCH /api/v1/integrations/{id}` — обновить интеграцию (только admin).
- `GET /api/v1/projects` — публичные проекты портфолио (авторизованным — и приватные).
- `GET /api/v1/projects/{slug}` — карточка проекта.
- `GET /api/v1/projects/all` — все проекты (admin).
- `POST/PATCH/DELETE /api/v1/projects` — управление портфолио (admin).

Пример логина:

```bash
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## Доступные CLI-команды на фронтенде

- `help` — список доступных команд.
- `login <логин> <пароль>` — авторизация.
- `register <логин> <пароль>` — регистрация и вход в сессию.
- `logout` — выход из системы.
- `reset-request <логин>` — запрос токена сброса пароля.
- `reset-password <токен> <новый_пароль>` — сброс пароля по токену.
- `password <текущий> <новый>` — смена пароля (нужна авторизация).
- `projects` — список проектов (после авторизации).
- `services` / `go` — список внешних сервисов.
- `go <сервис>` — открыть внешний сервис в новой вкладке (например `go github`, `go grafana`).
- `projects` / `project <slug>` — портфолио в терминале (гостям — public).
- `clear` — очистка экрана терминала.

### Портфолио

Проекты хранятся в БД. Публичные страницы:

- `http://localhost/projects` — список
- `http://localhost/projects/<slug>` — карточка проекта
- `http://localhost/admin/projects` — admin CRUD (только admin)

Приватные проекты (`is_public: false`) видны только после login.

### Интеграции (go / services)

Интеграции хранятся в PostgreSQL (таблица `integration`). При первом запуске сидируются дефолты: `github`, `gitlab`, `grafana`, `swagger`.

**Admin** (`admin` / `admin123`) управляет списком через REST API или Swagger (`/api/docs`).

Дополнительно `INTEGRATIONS_JSON` на backend накладывается поверх БД (удобно для Docker без правки данных):

```json
{
  "grafana": {"url": "http://localhost:3001", "requires_auth": true, "label": "Grafana"},
  "portainer": {"url": "http://localhost:9000", "requires_auth": true, "label": "Portainer"}
}
```

При успешном `go <сервис>` API возвращает `action: "open_url"` и `url` — фронтенд открывает ссылку в новой вкладке.

**Админ-панель:** `http://localhost/admin/integrations` (только для `is_admin`).

### RBAC в терминале

Роли: `guest` → `user` (после login) → `admin` (`admin` пользователь).

| Команда | Минимальная роль |
|---------|------------------|
| `help`, `services`, `go` (public) | guest |
| `projects` | user |
| `integrations` | admin |

При недостатке прав API возвращает `forbidden: true` или `requires_auth: true`.

### Миграции (Alembic)

Схема БД управляется через Alembic. При старте backend автоматически выполняется `alembic upgrade head`.

```bash
cd backend
python -m alembic upgrade head          # применить миграции
python -m alembic revision -m "описание" --autogenerate  # новая миграция
```

Для тестов используется SQLite + `create_all` (без Alembic).

### Безопасность auth (этап 2)

- JWT в **httpOnly cookies** (`credentials: include` на фронте)
- Вход через **форму** (`login` / `register` в терминале открывают модалку, пароль не попадает в историю команд)
- `ALLOW_REGISTRATION=false` по умолчанию (в docker-compose для dev: `true`)
- `EXPOSE_RESET_TOKEN=false` по умолчанию — токен сброса не отдаётся в API
- Rate limit на auth-эндпоинты (`AUTH_RATE_LIMIT_PER_MINUTE`)
- Секреты — через `.env` (см. `.env.example`)

### SSO lite (этап 3)

Интеграция с `use_sso: true` при `go <service>` добавляет `?sso_code=...` к URL.

Целевой сервис обменивает код:

```bash
POST /api/v1/auth/sso/exchange
{"code": "<sso_code>"}
# → {"username": "...", "access_token": "..."}
```

Код одноразовый, срок жизни — `SSO_CODE_EXPIRE_SECONDS` (по умолчанию 60 сек).

### OIDC Provider (полноценный)

Discovery: `GET /api/v1/oidc/.well-known/openid-configuration`

| Endpoint | Назначение |
|----------|------------|
| `/api/v1/oidc/authorize` | Authorization Code flow |
| `/api/v1/oidc/token` | Обмен code на tokens (RS256) |
| `/api/v1/oidc/userinfo` | Профиль по access token |
| `/api/v1/oidc/jwks` | Публичные ключи |
| `/api/v1/oidc/clients` | Admin CRUD OAuth клиентов |

Dev-клиент по умолчанию: `personal-me-dev` / `dev-secret-change-me`  
Redirect URI: `http://localhost/oauth/callback`

Пример authorize URL:

```
http://localhost/api/v1/oidc/authorize?response_type=code&client_id=personal-me-dev&redirect_uri=http://localhost/oauth/callback&scope=openid%20profile&state=xyz&nonce=abc
```

### CI

GitHub Actions: `.github/workflows/ci.yml` — pytest (backend) + vitest + build (frontend).

## Текстовая схема архитектуры

1. Пользователь открывает `Nginx` на `localhost`.
2. `Nginx` проксирует:
   - `/` -> `Nuxt 3 frontend`
   - `/api/*` -> `FastAPI backend`
3. Frontend отправляет terminal-команды в `POST /api/v1/terminal/execute`.
4. Backend:
   - валидирует запрос;
   - при необходимости проверяет JWT;
   - вызывает сервис обработки команд;
   - возвращает текстовый ответ.
5. Данные и модели хранятся в `PostgreSQL` через `SQLModel`.

## Локальная разработка без Docker

### Backend

```bash
cd backend
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Ближайшие шаги развития

- Email-отправка для reset password.
- Расширить OIDC (refresh tokens, consent UI, client credentials).
