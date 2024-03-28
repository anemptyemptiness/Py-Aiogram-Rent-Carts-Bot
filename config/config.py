from dataclasses import dataclass
from aiogram.fsm.storage.redis import Redis
from environs import Env


@dataclass
class TgBot:
    token: str


@dataclass
class Config:
    tg_bot: TgBot
    redis: Redis
    user_db: str
    password_db: str
    database: str
    host_db: str
    port_db: str

    host_mdb: str
    port_mdb: str
    db_name_mdb: str
    today_mdb: str
    carts_today_mdb: str

    employees: list
    admins: list
    count_carts: int


def load_config() -> Config:
    env = Env()
    env.read_env()

    return Config(
        tg_bot=TgBot(token=env("TOKEN")),
        redis=Redis(host=f"{env('redis_host')}"),
        employees=[int(f"{env(f'employee_{i}')}") for i in range(1, 3)],
        admins=[int(f"{env(f'admin_{i}')}") for i in range(1, 2)],
        user_db=env("user"),
        password_db=env("password"),
        database=env("database"),
        host_db=env("host"),
        port_db=env("port"),
        host_mdb=env("host_mongo"),
        port_mdb=env("port_mongo"),
        today_mdb=env("today_mongo"),
        carts_today_mdb=env("carts_mongo"),
        db_name_mdb=env("db_name_mongo"),
        count_carts=int(env("count_carts")),
    )


config: Config = load_config()
