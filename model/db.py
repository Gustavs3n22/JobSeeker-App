import os
import time
import psycopg2
from psycopg2 import OperationalError

LOCAL_DB_CONFIG = {
    "DB_HOST": "db",
    "DB_PORT": "5432",
    "DB_NAME": "HeadHunterHub",
    "DB_USER": "postgres",
    "DB_PASSWORD": "123123",
}


def get_db_connection(max_retries=12, delay=2):
    host = os.getenv("DB_HOST", LOCAL_DB_CONFIG["DB_HOST"])
    port = os.getenv("DB_PORT", LOCAL_DB_CONFIG["DB_PORT"])
    dbname = os.getenv("DB_NAME", LOCAL_DB_CONFIG["DB_NAME"])
    user = os.getenv("DB_USER", LOCAL_DB_CONFIG["DB_USER"])
    password = os.getenv("DB_PASSWORD", LOCAL_DB_CONFIG["DB_PASSWORD"])

    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port,
                connect_timeout=5
            )
            print(f"DB connected successfully (attempt {attempt + 1})")
            return conn
        except OperationalError as e:
            if attempt == max_retries - 1:
                print(f"Failed to connect after {max_retries} attempts: {e}")
                raise
            print(f"DB not ready yet (attempt {attempt + 1}/{max_retries}). Retrying in {delay}s...")
            time.sleep(delay)
    raise Exception("Could not connect to database after retries")