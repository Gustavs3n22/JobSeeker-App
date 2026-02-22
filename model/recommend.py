from fastapi import FastAPI
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine
import psycopg2
from model.db import get_db_connection

app=FastAPI()

class RecommendSystem:
    @classmethod
    def recommend(cls, user_id: int | None = None, selected_profile=None):
        if selected_profile not in ["data-analyst", "web"]:
            selected_profile = "data-analyst"

        DATABASE_URL = "postgresql+psycopg2://postgres:123123@localhost:5432/HeadHunterHub"
        engine = create_engine(DATABASE_URL)

        conn = get_db_connection()

        query = """
        SELECT v.title, v.employer AS company,
            STRING_AGG(s.title, ' , ') AS skills_str,
            v.url
        FROM vacancies v
        JOIN vacancyskills vs ON v.vacancy_id = vs.vacancy_id
        JOIN skills s ON vs.skill_id = s.skill_id
        AND s.title NOT IN (
            'Опыт 1-3 года', 'Опыт 3-6 лет', 'Выплаты: два раза в месяц',
            'Отклик без резюме', 'Откликнитесь среди первых', 'Без опыта',
            'Выплаты: раз в неделю', 'Выплаты: ежедневно', 'Выплаты: раз в месяц',
            'Можно удалённо', 'Выплаты: за проект', 'Подработка'
        )
        GROUP BY v.vacancy_id, v.title, v.employer, v.url
        """

        df = pd.read_sql_query(query, con=engine)
        cur = conn.cursor()

        df.replace("",np.nan,inplace=True)
        df.dropna(how="any",inplace=True)
        df.reset_index(drop=True,inplace=True)

        model = SentenceTransformer("/app/models/all-MiniLM-L6-v2")

        skill_embeddings=model.encode(df['skills_str'].tolist(),batch_size=6,show_progress_bar=True,normalize_embeddings=True)

        get_user_skills = """
        SELECT s.title
        FROM users u
        JOIN userskills us ON u.user_id = us.user_id
        JOIN skills s ON us.skill_id = s.skill_id
        WHERE u.user_id = %s
        """
        uid = user_id or 1
        print(uid) # debug
        cur.execute(get_user_skills, (uid,))
        rows = cur.fetchall()

        if not rows:
            user_skills = ['MS Excel']
        else:
            user_skills = [{"label": row[0]} for row in rows]

        conn.close()

        user_input_embedding=model.encode(user_skills,normalize_embeddings=True)
        user_similarities=cosine_similarity(user_input_embedding,skill_embeddings)[0]
        top_indices=np.argsort(user_similarities)[::-1]

        conn.close()
        recommendations=[]
        for i,idx in enumerate(top_indices,1):
            if idx<df.shape[0]:
                sim=user_similarities[idx]
                recommendations.append({'rank':i,'title':df.iloc[idx]['title'],'similarity':sim,'company':df.iloc[idx]['company'],'skills':df.iloc[idx]['skills_str'][:150]+'...','url':df.iloc[idx]['url']})

        return recommendations