from fastapi import FastAPI
import psycopg2
from model.db import get_db_connection

app=FastAPI()

class Profile:
    @classmethod
    def get_chips(cls):
        conn = get_db_connection()
        cur = conn.cursor()

        get_chips = """
        select title, skill_id from skills 
        where title not in (
            'Опыт 1-3 года', 'Опыт 3-6 лет', 'Выплаты: два раза в месяц', 'Отклик без резюме', 
            'Откликнитесь среди первых', 'Без опыта', 'Выплаты: раз в неделю', 'Выплаты: ежедневно',
            'Выплаты: раз в месяц', 'Можно удалённо', 'Выплаты: за проект', 'Подработка')
        """
        
        cur.execute(get_chips)
        rows = cur.fetchall() 

        chips = [{"label": title, "value": skill_id} for title, skill_id in rows]
        conn.close()

        return chips
            
    @classmethod
    def apply_chips(cls, user_id, ids):
        conn = psycopg2.connect(
            dbname='HeadHunterHub',
            user='postgres',
            password='123123',
            host='localhost',
            port='5432'
        )
        cur = conn.cursor()

        for skill_id in ids:
            cur.execute(
                "insert into userskills (skill_id, user_id) values (%s, %s)",
                (skill_id, user_id)
            )
        conn.commit()
        conn.close()

        return "ok"
    
    @classmethod
    def search_profile(cls, user_id):
        conn = psycopg2.connect(
            dbname='HeadHunterHub',
            user='postgres',
            password='123123',
            host='localhost',
            port='5432'
        )
        cur = conn.cursor()

        get_profile = """
        SELECT s.title, s.skill_id
        FROM users u
        JOIN userskills us ON u.user_id = us.user_id
        JOIN skills s ON us.skill_id = s.skill_id
        WHERE u.user_id = %s
        """

        cur.execute(get_profile, (user_id,))
        rows = cur.fetchall()

        user_chips = [{"label": title, "value": skill_id} for title, skill_id in rows]
        conn.close()

        return user_chips