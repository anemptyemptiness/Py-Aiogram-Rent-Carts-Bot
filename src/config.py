from aiogram.fsm.storage.redis import Redis
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TOKEN: str

    ADMIN_ID: int

    REDIS_HOST: str

    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int

    DAYS_FOR_FINANCES_CHECK: int

    @property
    def get_url_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    MONGODB_HOST: str
    MONGODB_PORT: int
    MONGODB_NAME: str
    MONGODB_TODAY: str
    MONGODB_CARTS_TODAY: str
    MONGODB_COUNT_CARTS: int

    class Config:
        env_file = "../.env"


settings = Settings()
redis = Redis(host=settings.REDIS_HOST)
