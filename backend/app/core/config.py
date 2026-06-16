import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./compliance.db"
    JWT_SECRET_KEY: str = "dev_secret_key_change_me_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS Origins can be input as a comma-separated string or list
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("CORS_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    def validate_production_settings(self) -> None:
        """Raise error in non-dev env if secrets are insecure or default."""
        if self.ENV != "dev":
            if self.DATABASE_URL == "sqlite:///./compliance.db":
                raise ValueError("In production, DATABASE_URL must point to a production-grade database (e.g. PostgreSQL).")
            if self.JWT_SECRET_KEY == "dev_secret_key_change_me_in_production":
                raise ValueError("In production, JWT_SECRET_KEY must be a cryptographically secure value.")

settings = Settings()

# Validate configuration on startup
settings.validate_production_settings()
