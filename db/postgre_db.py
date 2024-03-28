from config.config import Config
import psycopg2


class DataBase:
    def __init__(self, config: Config):
        self._user = config.user_db
        self._password = config.password_db
        self._database = config.database
        self._host = config.host_db
        self._port = config.port_db

    def connect_to_db(self):
        connect = psycopg2.connect(
            dbname=self._database,
            user=self._user,
            password=self._password,
            host=self._host,
            port=self._port
        )

        return connect

    def get_users(self):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute("SELECT user_id FROM users;")
            user_ids = cursor.fetchall()
            return user_ids
        except Exception as e:
            print("Error with SELECT:", e)
        finally:
            cursor.close()
            connect.close()

    def add_users(self, user_id: int, fullname: str) -> None:
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(f"INSERT INTO users (user_id, fullname) VALUES ({user_id}, '{fullname}');")
            connect.commit()
        except Exception as e:
            print("Error with INSERT:", e)
        finally:
            cursor.close()
            connect.close()

    def user_exists(self, user_id) -> bool:
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(f"SELECT user_id FROM users WHERE user_id = {user_id};")
            user_id = cursor.fetchone()
            return True if user_id else False
        except Exception as e:
            print("Error with CHECK EXISTS:", e)
        finally:
            cursor.close()
            connect.close()