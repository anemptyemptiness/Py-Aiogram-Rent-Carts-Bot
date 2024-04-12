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

    def get_current_name(self, user_id: int):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT e.fullname "
                "FROM employees AS e "
                f"WHERE e.user_id = {user_id};"
            )
            name = cursor.fetchone()
            return name[0]
        except Exception as e:
            print("DB: get_current_name() error:", e)
        finally:
            cursor.close()
            connect.close()

    def get_admins_user_ids(self):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT user_id "
                "FROM admins;"
            )
            admins = [x[0] for x in cursor.fetchall()]
            return admins
        except Exception as e:
            print("DB: get_admins_user_ids() error:", e)
        finally:
            cursor.close()
            connect.close()

    def get_employees_user_ids(self):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT user_id "
                "FROM employees;"
            )
            employees = [x[0] for x in cursor.fetchall()]
            return employees
        except Exception as e:
            print("DB: get_employees_user_ids() error:", e)
        finally:
            cursor.close()
            connect.close()

    def get_chat_ids(self):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT chat_id "
                "FROM places;"
            )
            chat_ids = [x[0] for x in cursor.fetchall()]
            return chat_ids
        except Exception as e:
            print("DB: get_chat_ids() error:", e)
        finally:
            cursor.close()
            connect.close()

    def get_titles_places(self):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT place "
                "FROM places;"
            )
            titles = [x[0] for x in cursor.fetchall()]
            return titles
        except Exception as e:
            print("DB: get_titles_places() error:", e)
        finally:
            cursor.close()
            connect.close()

    def add_employee(self, fullname, user_id, username):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "INSERT INTO employees (fullname, user_id, username) "
                f"VALUES ('{fullname}', {user_id}, '{username}') "
                "ON CONFLICT (user_id) DO UPDATE "
                "SET fullname = excluded.fullname,"
                "username = excluded.username;"
            )
            connect.commit()
        except Exception as e:
            print("DB: add_employee() error:", e)
        finally:
            cursor.close()
            connect.close()

    def add_admin(self, fullname, user_id, username):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "INSERT INTO admins (fullname, user_id, username) "
                f"VALUES ('{fullname}', {user_id}, '{username}') "
                "ON CONFLICT (user_id) DO UPDATE "
                "SET fullname = excluded.fullname,"
                "username = excluded.username;"
            )
            connect.commit()

            self.add_employee(
                user_id=user_id,
                fullname=fullname,
                username=username,
            )
        except Exception as e:
            print("DB: add_admin() error:", e)
        finally:
            cursor.close()
            connect.close()

    def add_place(self, title, chat_id, count_carts):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "INSERT INTO places (place, chat_id, count_carts) "
                f"VALUES ('{title}', {chat_id}, {count_carts}) "
                "ON CONFLICT (chat_id) DO UPDATE "
                "SET place = excluded.place, "
                "count_carts = excluded.count_carts;"
            )
            connect.commit()
        except Exception as e:
            print("DB: add_place() error:", e)
        finally:
            cursor.close()
            connect.close()

    def get_employees_fullnames_ids(self):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT fullname, user_id "
                "FROM employees;"
            )
            employees = [(x[0], x[1]) for x in cursor.fetchall()]
            return employees
        except Exception as e:
            print("DB: get_employees_fullnames_ids() error:", e)
        finally:
            cursor.close()
            connect.close()

    def get_current_employee_by_id(self, user_id):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT fullname, username "
                "FROM employees "
                f"WHERE user_id = {user_id};"
            )
            employees_data = cursor.fetchone()
            return employees_data[0], employees_data[1]
        except Exception as e:
            print("DB: get_current_employee_by_id() error:", e)
        finally:
            cursor.close()
            connect.close()

    def get_admins_fullnames_ids(self):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT fullname, user_id "
                "FROM admins;"
            )
            admins = [(x[0], x[1]) for x in cursor.fetchall()]
            return admins
        except Exception as e:
            print("DB: get_admins_fullnames_ids() error:", e)
        finally:
            cursor.close()
            connect.close()

    def get_current_admin_by_id(self, user_id):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT fullname, username "
                "FROM admins "
                f"WHERE user_id = {user_id};"
            )
            admins_data = cursor.fetchone()
            return admins_data[0], admins_data[1]
        except Exception as e:
            print("DB: get_current_admin_by_id() error:", e)
        finally:
            cursor.close()
            connect.close()

    def get_places_chat_ids(self):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT place, chat_id "
                "FROM places;"
            )
            places = [(x[0], x[1]) for x in cursor.fetchall()]
            return places
        except Exception as e:
            print("DB: get_places_chat_ids() error:", e)
        finally:
            cursor.close()
            connect.close()

    def get_place_count_carts(self, place):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT count_carts "
                "FROM places "
                f"WHERE place='{place}';"
            )
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            print("DB: get_place_count_carts() error:", e)
        finally:
            cursor.close()
            connect.close()

    def get_places_chat_id_title_count_carts(self):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "SELECT chat_id, place, count_carts "
                "FROM places;"
            )
            count = cursor.fetchall()
            return count
        except Exception as e:
            print("DB: get_places_chat_id_title_count_carts() error:", e)
        finally:
            cursor.close()
            connect.close()

    def delete_employee(self, fullname, username):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "DELETE FROM employees "
                f"WHERE fullname='{fullname}' AND username='{username}';"
            )
            connect.commit()
        except Exception as e:
            print("DB: delete_employee() error:", e)
        finally:
            cursor.close()
            connect.close()

    def delete_admin(self, fullname, username):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "DELETE FROM admins "
                f"WHERE fullname='{fullname}' AND username='{username}';"
            )
            connect.commit()

            self.delete_employee(
                fullname=fullname,
                username=username,
            )
        except Exception as e:
            print("DB: delete_admin() error:", e)
        finally:
            cursor.close()
            connect.close()

    def delete_place(self, title):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                "DELETE FROM places "
                f"WHERE place='{title}';"
            )
            connect.commit()
        except Exception as e:
            print("DB: delete_place() error:", e)
        finally:
            cursor.close()
            connect.close()