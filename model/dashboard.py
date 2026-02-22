from fastapi import FastAPI
import psycopg2
from model.db import get_db_connection

app = FastAPI()

class GetDashboard:
    @classmethod
    def get_dashboard(cls):
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # vacancies
            cur.execute("select count(*) from vacancies;")
            vacancies = cur.fetchone()[0]

            # skills
            cur.execute("select count(*) from skills")
            skills = cur.fetchone()[0]

            # companies
            cur.execute("select count(distinct employer) from vacancies;")
            companies = cur.fetchone()[0]

            # users
            cur.execute("select count(*) from users;")
            users = cur.fetchone()[0]

            # vacancy per company ratio
            ratio = round(vacancies / companies, 1)

            dashboard = {
                "vacancies": vacancies,
                "skills": skills,
                "companies": companies,
                "users": users,
                "ratio": ratio
            }

        except Exception as e:
            dashboard = {
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

            return dashboard