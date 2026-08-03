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
