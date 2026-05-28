# API Reference (Initial)

## Auth

### POST `/api/v1/auth/login`

Request body:

```json
{
  "username": "admin",
  "password": "admin123"
}
```

Response:

```json
{
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token",
  "token_type": "bearer"
}
```

### POST `/api/v1/auth/register`

Request body:

```json
{
  "username": "newuser",
  "password": "newuser123"
}
```

Response:

```json
{
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token",
  "token_type": "bearer"
}
```

### POST `/api/v1/auth/refresh`

Request body:

```json
{
  "refresh_token": "jwt-refresh-token"
}
```

Response:

```json
{
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token-rotated",
  "token_type": "bearer"
}
```

### POST `/api/v1/auth/logout`

Request body:

```json
{
  "refresh_token": "jwt-refresh-token"
}
```

Response: `204 No Content`

## Terminal

### POST `/api/v1/terminal/execute`

Request body:

```json
{
  "command": "help"
}
```

Response:

```json
{
  "command": "help",
  "output": "Available commands: help, login, projects, clear",
  "requires_auth": false
}
```

Known commands:

- `help`
- `login`
- `register`
- `logout`
- `projects` (requires auth)
- `clear`
