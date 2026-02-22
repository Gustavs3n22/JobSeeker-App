from fastapi import FastAPI
from model.db import get_db_connection

app = FastAPI()


class GetDashboard:
    @classmethod
    def get_dashboard(cls):
        conn = None
        cur = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT count(*) FROM vacancies;")
            vacancies = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM skills;")
            skills = cur.fetchone()[0]

            cur.execute("SELECT count(DISTINCT employer) FROM vacancies;")
            companies = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM users;")
            users = cur.fetchone()[0]

            ratio = round(vacancies / companies, 1) if companies else 0

            return {
                "vacancies": vacancies,
                "skills": skills,
                "companies": companies,
                "users": users,
                "ratio": ratio
            }

        except Exception as e:
            print(f"Dashboard DB Error: {type(e).__name__}: {e}")
            return {
                "vacancies": "err",
                "skills": "err",
                "companies": "err",
                "users": "err",
                "ratio": "err"
            }
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()