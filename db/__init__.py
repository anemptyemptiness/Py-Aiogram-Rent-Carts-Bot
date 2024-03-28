from config.config import config
from db.postgre_db import DataBase
from db.mongo_db import MongoDB

DB = DataBase(config=config)
DB_mongo = MongoDB(config=config)