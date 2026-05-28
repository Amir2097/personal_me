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
- `POST /api/v1/terminal/execute` — выполнение terminal-команды.

Пример логина:

```bash
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## Доступные CLI-команды на фронтенде

- `help` — список доступных команд.
- `login <username> <password>` — получить JWT и активировать защищенные команды.
- `register <username> <password>` — создать аккаунт и сразу получить сессию.
- `logout` — завершить сессию и очистить локальные токены.
- `projects` — список проектов (доступно после авторизации).
- `clear` — очистка экрана терминала.

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

- Добавить регистрацию пользователей и reset password flow.
- Добавить роли/права на команды терминала.
- Расширить тесты (`pytest`, `vitest`) и CI pipeline.
