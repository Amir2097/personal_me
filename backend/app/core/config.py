"""Application settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    app_name: str = "Personal Me Terminal API"
    api_v1_prefix: str = "/api/v1"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    password_reset_expire_minutes: int = 30
    postgres_dsn: str = "postgresql+psycopg://app:app@db:5432/personal_me"
    initial_admin_username: str = "admin"
    initial_admin_password: str = "admin123"
    initial_admin_email: str = ""
    integrations_json: str = "{}"
    allow_registration: bool = False
    expose_reset_token: bool = False
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_domain: str = ""
    auth_cookie_path: str = "/"
    cors_origins: str = "http://localhost"
    auth_rate_limit_per_minute: int = 30
    sso_code_expire_seconds: int = 60
    oidc_issuer: str = "http://localhost/api/v1/oidc"
    oidc_frontend_base_url: str = "http://localhost"
    oidc_auto_approve: bool = True
    oidc_private_key_pem: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@localhost"
    smtp_use_tls: bool = True
    feedback_to_email: str = ""
    feedback_rate_limit_per_minute: int = 5
    site_owner_name: str = ""
    site_tagline: str = (
        "Интерактивный командный центр: портфолио, интеграции и сервисы в одном терминале."
    )
    site_bio: str = (
        "Backend-разработчик. Строю developer hub с терминальным UI, "
        "JWT-auth, OIDC и интеграциями сервисов."
    )
    site_skills: str = "Python, FastAPI, PostgreSQL, Nuxt, Docker, OIDC"
    site_experience: str = ""
    site_github_url: str = ""
    site_telegram: str = ""
    site_resume_url: str = ""
    site_motd: str = "Добро пожаловать. Введите help или откройте projects."
    site_url: str = "http://localhost"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
