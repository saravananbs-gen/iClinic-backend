from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    GROQ_API_KEY: str
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    REDIS_HOST: str
    REDIS_PORT: str
    LANGSMITH_TRACING: str
    LANGSMITH_ENDPOINT: str
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRES_MINUTES: int
    REFRESH_TOKEN_EXPIRES_MINUTES: int
    REFRESH_COOKIE_NAME: str
    REFRESH_COOKIE_SAMESITE: str
    REFRESH_COOKIE_SECURE: bool
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_EMAIL: str
    SMTP_APP_PASSWORD: str

    class Config:
        env_file = ".env"


settings = Settings()
