from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    REDIS_URL: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


def get_settings():
    """
    Get settings instance.
    This allows for overriding settings in tests.
    """
    return Settings()


# Global settings instance
settings = get_settings()
