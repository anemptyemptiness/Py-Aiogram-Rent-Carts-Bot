import logging

from src.config import Settings
import psycopg2


class DataBase:
    def __init__(self, settings: Settings):
        self._user = settings.DB_USER
        self._password = settings.DB_PASS
        self._database = settings.DB_NAME
        self._host = settings.DB_HOST
        self._port = settings.DB_PORT
        self._logger = logging.getLogger(__name__)

    def _connect_to_db(self):
        connect = psycopg2.connect(
            dbname=self._database,
            user=self._user,
            password=self._password,
            host=self._host,
            port=self._port
        )

        return connect

    def get_admins_user_ids(self):
        connect = self._connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT user_id "
                "FROM employees "
                "WHERE role = 'admin';"
            )
            admins = [x[0] for x in cursor.fetchall()]
            return admins
        except Exception as e:
            self._logger.exception("Ошибка в get_admins_user_ids() postgre_db.py")
        finally:
            cursor.close()
            connect.close()

    def get_employees_user_ids(self):
        connect = self._connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT user_id "
                "FROM employees "
                "WHERE role = 'employee';"
            )
            employees = [x[0] for x in cursor.fetchall()]
            return employees
        except Exception as e:
            self._logger.exception("Ошибка в get_employees_user_ids() postgre_db.py")
        finally:
            cursor.close()
            connect.close()

    def get_chat_ids(self):
        connect = self._connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT chat_id "
                "FROM places;"
            )
            chat_ids = [x[0] for x in cursor.fetchall()]
            return chat_ids
        except Exception as e:
            self._logger.exception("Ошибка в get_chat_ids() postgre_db.py")
        finally:
            cursor.close()
            connect.close()

    def get_places(self):
        connect = self._connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                """
                SELECT p.title, p.chat_id 
                FROM places AS p;
                """
            )
            return [(x[0], x[1]) for x in cursor.fetchall()]
        except Exception as e:
            self._logger.exception("Ошибка в get_places() postgre_db.py")
        finally:
            cursor.close()
            connect.close()

    def get_employees_fullname_and_id(self, role: str):
        connect = self._connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                f"""
                SELECT e.fullname, e.user_id 
                FROM employees AS e 
                WHERE role = '{role}';
                """
            )
            return [(x[0], x[1]) for x in cursor.fetchall()]
        except Exception as e:
            self._logger.exception("Ошибка в get_employees_fullname_and_id() postgre_db.py")
        finally:
            cursor.close()
            connect.close()
