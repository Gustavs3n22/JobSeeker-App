from fastapi import FastAPI
import psycopg2
from model.db import get_db_connection

app=FastAPI()

class Register:
    @classmethod
    def reg(cls, username, password):
        conn = get_db_connection()
        cur = conn.cursor()

        insert_user = """
        insert into users (user_name, user_password, business_role)
        values (%s, %s, %s);
        """

        cur.execute(insert_user, (username, password, 1))
        conn.commit()
        conn.close()

        return "ok"