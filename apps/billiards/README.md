# Billiards Kolkhoz Manager

Offline-first Nuxt 3 подсервис DAUTOVTECH для игры «Колхоз».

## Локально

```bash
cd apps/billiards
npm install
npm run dev
```

Откроется на `http://localhost:3010/billiards/`.

## Docker

Сервис `billiards` в корневом `docker-compose.yml`, nginx: `/billiards/`.

## Режимы

- `/billiards/` — выбор режима
- `/billiards/casual` — быстрый стол
- `/billiards/tournament` — турнир
- `/billiards/tv` — TV-табло

Состояние в `localStorage` (`dautovtech_kolkhoz_v1`).

## Авторизация

- Страница хаба `/hobby` публичная; запуск Kolkhoz требует login.
- `go billiards` / кнопка на `/hobby` открывают URL с одноразовым `sso_code`.
- Middleware billiards обменивает код (или проверяет cookie/JWT через `/auth/me`).
- Гостей перенаправляет на `/hobby?auth=required`.

## Синк телефон ↔ TV

1. На пульте (`/tournament/play`) блок **Синк** → «Открыть синк» (нужна авторизация).
2. Появится код комнаты — откройте на TV `/billiards/tv?room=КОД` или введите код на табло.
3. Хост пушит состояние при каждом изменении; TV опрашивает API ~раз в секунду.
4. API: `POST/PUT/GET /api/v1/kolkhoz/sessions`.

## История партий

Снимки на сервере под аккаунтом хаба:

- `POST /api/v1/kolkhoz/games` — сохранить текущую партию
- `GET /api/v1/kolkhoz/games` — список
- `GET /api/v1/kolkhoz/games/{id}` — загрузить state
- `DELETE /api/v1/kolkhoz/games/{id}` — удалить

На главной Kolkhoz и на пультах — блок **История партий**.

## Академия — прогресс

Результаты упражнений:

- локально в `localStorage` (`billiards_academy_progress_v1`);
- при входе через хаб — синк с `GET/PUT /api/v1/academy/progress` (новее по `updated_at` побеждает).
