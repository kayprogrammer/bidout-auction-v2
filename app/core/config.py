from pathlib import Path
from typing import Dict, Optional

from pydantic import AnyHttpUrl, AnyUrl, BaseSettings, EmailStr, validator

PROJECT_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    # DEBUG
    DEBUG: bool

    # TOKENS
    EMAIL_OTP_EXPIRE_MINUTES: int
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int

    # SECURITY
    SECRET_KEY: str

    # PROJECT NAME, API PREFIX, CORS ORIGINS
    PROJECT_NAME: str
    FRONTEND_URL: str

    # POSTGRESQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URL: Optional[str] = None

    # FIRST SUPERUSER
    FIRST_SUPERUSER_EMAIL: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    # FIRST AUCTIONEER
    FIRST_AUCTIONEER_EMAIL: EmailStr
    FIRST_AUCTIONEER_PASSWORD: str

    # FIRST REVIEWER
    FIRST_REVIEWER_EMAIL: EmailStr
    FIRST_REVIEWER_PASSWORD: str

    # EMAIL CONFIG
    MAIL_SENDER: str
    MAIL_SENDER_PASSWORD: str
    MAIL_SEND_HOST: str
    MAIL_SEND_PORT: int
    MAIL_TLS: bool
    MAIL_START_TLS: bool
    MAIL_CONFIG: Optional[dict] = None

    @validator("SQLALCHEMY_DATABASE_URL", pre=True)
    def assemble_postgres_connection(
        cls, v: Optional[str], values: Dict[str, str]
    ) -> str:
        if isinstance(v, str):
            return v
        if values.get("DEBUG"):
            postgres_server = "localhost"
        else:
            postgres_server = values.get("POSTGRES_SERVER")

        return AnyUrl.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=postgres_server or "localhost",
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB')}",
        )

    @validator("MAIL_CONFIG", pre=True)
    def assemble_mail_config(cls, v, values):
        return {
            "MAIL_SENDER": values.get("MAIL_SENDER"),
            "MAIL_SENDER_PASSWORD": values.get("MAIL_SENDER_PASSWORD"),
            "MAIL_SEND_HOST": values.get("MAIL_SEND_HOST"),
            "MAIL_SEND_PORT": values.get("MAIL_SEND_PORT"),
            "MAIL_TLS": values.get("MAIL_TLS"),
            "MAIL_START_TLS": values.get("MAIL_START_TLS"),
        }

    class Config:
        env_file = f"{PROJECT_DIR}/.env"
        case_sensitive = True


settings: Settings = Settings()
