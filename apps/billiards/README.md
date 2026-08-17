# Цифровое Сукно

Nuxt-приложение: колхоз, олимпийская сетка, академия, табло.
Бренд фиксированный — **Цифровое Сукно**. Контур клуба (своё имя, тенант) пока не заводится: клубы позже получат внутренний
функционал, без смены вывески. SEO установки настраивается в `/admin`.

Карта выноса: `docs/architecture/billiards-product.md`.
API: `apps/billiards-api`.

## Локально

```bash
cd apps/billiards
npm install
npm run dev
```

Откроется на `http://localhost:3010/billiards/` без редиректа на логин
(префикс хаба). Для своего домена: `NUXT_APP_BASE_URL=/` — тогда главная это `/`.

## Docker

- Основной стек (dev): `billiards` + `billiards-api` в корневом `docker-compose.yml`, nginx `/billiards/`.
- Standalone **prod** (главная `/`, без хаба):

```bash
docker compose -f docker-compose.billiards.yml up --build
```

  → UI `http://localhost:8080/`, API docs `http://localhost:8010/api/sukno/docs`.

Сборка только образа UI:

```bash
docker build -f apps/billiards/Dockerfile.prod -t sukno-ui ./apps/billiards
```

## Режимы

- `/` — главная
- `/casual`, `/tournament` — колхоз
- `/cup` — сетка
- `/academy` — тренажёр
- `/tv` — табло (просмотр комнаты без входа)
- `/admin` — SEO и настройки сайта (аккаунт admin; dev: опционально `SUKNO_ADMIN_KEY`)

Состояние игры: `localStorage`.

Бренд: `public/favicon.svg`, `public/brand/logo.svg` (светлый фон),
`public/brand/logo-on-dark.svg`, `public/brand/icon.png`.

## Авторизация

- Гость играет сразу (localStorage). Device JWT — для истории и академии, **не** для табло.
- Аккаунты Цифрового Сукна: `/auth/login`, роли player / operator / admin.
- Трансляция на табло — только **operator** или **admin**; просмотр `/tv` и `/cup/tv` — без входа.
- Опционально: вход через хаб DAUTOVTECH (`NUXT_PUBLIC_HUB_URL`) — кнопка на `/auth/login`.
- Регистрация скрывается, если API вернул `allow_registration: false`.
- 2FA (operator/admin): QR-код на `/profile` и `/admin/security`.
- Админка `/admin`: аккаунт admin или legacy-ключ в dev (`SUKNO_ADMIN_KEY`).

## Синк телефон ↔ TV

1. Оператор на пульте → **Создать комнату** (8 символов, TTL 12 ч).
2. TV `/tv?room=КОД` или `/cup/tv?room=КОД` — без входа.
3. Хост пушит состояние; табло опрашивает API ~1 раз/сек.
4. Турнир: пара с аккаунтом открывает ссылку матча, «Это я», вносит счёт — табло обновляется сразу. Оператор может перебить.
5. **QR** на пульте и `/tv` — отсканировать ссылку табло без ввода кода.
6. **Excel** турнира — кнопка на `/cup/bracket`; колхоз — на `/kolkhoz`.
7. **Автосохранение** колхоза в облако ~раз в 1,5 мин (при доступном API).

## История

- Турнирная сетка: локальные снимки + облако, если API доступен.
- Колхоз: облачные снимки через API; текущая партия и так в браузере.
