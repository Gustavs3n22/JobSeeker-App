from fastapi import FastAPI, Cookie
import psycopg2
from itsdangerous import URLSafeSerializer, BadSignature
from datetime import datetime
from typing import Optional
from model.db import get_db_connection

SECRET_KEY = "ef4b014340f36e975d26d90e4e425fdfa67e6487da1f49c45a678efd35218048"
COOKIE_NAME = "session"
COOKIE_MAX_AGE = 60 * 60 * 24 * 1  # 1 day

serializer = URLSafeSerializer(SECRET_KEY, salt="session-cookie")

app = FastAPI()

class Login:
    @classmethod
    def login(cls, username, userpassword):
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            select_user = """
            select user_id, user_name, user_password, business_role 
            from users where user_name = %s
            and user_password = %s limit 1
            """
            cur.execute(select_user, (username, userpassword))
            row = cur.fetchone()
            cur.close()
            conn.close()

            if not row:
                return None
            return row[0]
        finally:
            try:
                cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

    @classmethod
    def create_session_cookie_value(cls, user_id: int) -> str:
        payload = {"uid": user_id, "ts": int(datetime.utcnow().timestamp())}
        return serializer.dumps(payload)

    @classmethod
    def parse_session_cookie_value(cls, value: str) -> Optional[int]:
        try:
            payload = serializer.loads(value)
            return int(payload.get("uid"))
        except BadSignature:
            return None

    @classmethod
    def get_current_user_id(
        cls, 
        session: Optional[str] = Cookie(default=None, alias=COOKIE_NAME)
    ) -> Optional[int]:
        if not session:
            return None
        return cls.parse_session_cookie_value(session)