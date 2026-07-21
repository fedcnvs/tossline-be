from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"  # "development" or "production"

    database_url: str = "sqlite:///./tossline.db"

    jwt_secret: str = "change-me-to-a-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    pin_expire_minutes: int = 10

    email_backend: str = "console"  # "console" or "resend"
    resend_api_key: str = ""
    email_from: str = "login@tossline.example"

    admin_username: str = ""
    admin_password: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
