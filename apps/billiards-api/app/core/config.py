"""Цифровое Сукно API settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Цифровое Сукно API"
    api_v1_prefix: str = "/api/v1"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    refresh_token_expire_days: int = 7
    password_reset_expire_minutes: int = 30
    email_verification_expire_minutes: int = 60 * 24
    postgres_dsn: str = "postgresql+psycopg://app:app@db:5432/personal_me"
    cors_origins: str = "http://localhost,http://localhost:3000,http://localhost:3010"
    sukno_admin_key: str = ""
    allow_legacy_admin_key: bool = False
    frontend_base_url: str = "http://localhost/billiards"
    allow_registration: bool = True
    require_email_verification: bool = True
    auth_rate_limit_per_minute: int = 30
    initial_admin_username: str = "admin"
    initial_admin_password: str = "admin123"
    initial_admin_email: str = "admin@localhost"
    expose_reset_token: bool = False
    expose_verification_token: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@localhost"
    smtp_use_tls: bool = True
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_domain: str = ""
    auth_cookie_path: str = "/"
    totp_challenge_expire_minutes: int = 5
    totp_issuer: str = "Цифровое Сукно"
    uploads_dir: str = "uploads"
    avatar_max_bytes: int = 2 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
