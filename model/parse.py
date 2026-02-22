import requests
import time
from fastapi import FastAPI
from model.db import get_db_connection

app = FastAPI()

class SeedDatabase:
    @classmethod
    def seed(cls, max_pages: int = 10, detailed: bool = True, sleep_between: float = 0.8):
        """
        Seeding базы вакансиями и навыками с hh.ru API.
        
        Аргументы:
            max_pages      - ограничение по количеству страниц (защита от бесконечного цикла)
            detailed       - делать ли запрос на полную вакансию для получения key_skills (по умолчанию True)
            sleep_between  - пауза между запросами детальных вакансий (сек)
        """
        print("SEED DATABASE STARTED")
        conn = get_db_connection()
        cur = conn.cursor()
        conn.autocommit = False

        cur.execute("""
            TRUNCATE TABLE vacancyskills CASCADE;
            TRUNCATE TABLE skills CASCADE;
            TRUNCATE TABLE vacancies CASCADE;
        """)
        conn.commit()

        BASE_URL = "https://api.hh.ru/vacancies"
        HEADERS = {
            "HH-User-Agent": "VacancySeeder/1.0 (zinovvova3@gmail.com)",
            "User-Agent": "Mozilla/5.0 (compatible; VacancySeeder/1.0)"
        }

        params = {
            "area": 22,
            "search_field": ["name", "company_name", "description"],
            "excluded_text": "гравировщик, флорист",
            "professional_role": [25, 34, 96, 104, 116, 68, 170, 2, 73, 3, 103, 98],
            "per_page": 100,
            "page": 0,
        }

        page = 0
        total_processed = 0
        total_skills_found = 0

        while page < max_pages:
            print(f"→ Страница {page + 1}")
            current_params = params.copy()
            current_params["page"] = page

            try:
                resp = requests.get(BASE_URL, params=current_params, headers=HEADERS, timeout=12)
                resp.raise_for_status()
                data = resp.json()

                items = data.get("items", [])
                if not items:
                    print("  Нет больше вакансий → завершаем")
                    break

                pages_total = data.get("pages", 1)
                print(f"  Найдено вакансий на странице: {len(items)} | всего страниц: {pages_total}")

                for item in items:
                    vacancy_id = item.get("id")
                    if not vacancy_id:
                        continue

                    title = (item.get("name") or "").strip()
                    if not title:
                        continue

                    employer = item.get("employer", {}).get("name") or "Не указан"
                    experience = item.get("experience", {}).get("name", "")
                    link = item.get("alternate_url") or f"https://hh.ru/vacancy/{vacancy_id}"

                    try:
                        cur.execute("""
                            INSERT INTO vacancies (title, employer, experience, url)
                            VALUES (%s, %s, %s, %s)
                            RETURNING vacancy_id;
                        """, (title, employer, experience, link))
                        vacancy_db_id = cur.fetchone()[0]

                        skills = []

                        if detailed:
                            detail_url = f"https://api.hh.ru/vacancies/{vacancy_id}"
                            try:
                                time.sleep(sleep_between)
                                detail_resp = requests.get(detail_url, headers=HEADERS, timeout=8)
                                if detail_resp.status_code == 429:
                                    print("  429 Too Many Requests → ждём 60 сек...")
                                    time.sleep(60)
                                    detail_resp = requests.get(detail_url, headers=HEADERS, timeout=8)

                                detail_resp.raise_for_status()
                                full = detail_resp.json()
                                skills = full.get("key_skills", [])
                                print(f"  {title[:60]}... → навыков: {len(skills)}")
                            except requests.exceptions.HTTPError as http_err:
                                print(f"  Ошибка детального запроса {vacancy_id}: {http_err}")
                                skills = []
                            except Exception as e:
                                print(f"  Не удалось получить детали {vacancy_id}: {e}")
                                skills = []

                        else:
                            skills = item.get("key_skills", [])
                            if skills:
                                print(f"  (из списка) {title[:60]}... → навыков: {len(skills)}")

                        for skill in skills:
                            txt = (skill.get("name") or "").strip()
                            if not txt:
                                continue

                            cur.execute("""
                                INSERT INTO skills (title, skill_role)
                                VALUES (%s, 1)
                                ON CONFLICT (title) DO NOTHING
                                RETURNING skill_id;
                            """, (txt,))
                            row = cur.fetchone()

                            if row:
                                skill_id = row[0]
                            else:
                                cur.execute("SELECT skill_id FROM skills WHERE title = %s", (txt,))
                                skill_id = cur.fetchone()[0]

                            cur.execute("""
                                INSERT INTO vacancyskills (vacancy_id, skill_id)
                                VALUES (%s, %s)
                                ON CONFLICT DO NOTHING;
                            """, (vacancy_db_id, skill_id))

                            total_skills_found += 1

                        conn.commit()
                        total_processed += 1

                    except Exception as e:
                        conn.rollback()
                        print(f"ERROR processing vacancy {vacancy_id}: {e}")
                        continue

                page += 1

                if page >= pages_total:
                    print("  Достигнут конец страниц по данным API")
                    break

            except requests.exceptions.RequestException as e:
                print(f"API request failed on page {page + 1}: {e}")
                break
            except Exception as e:
                conn.rollback()
                print(f"Unexpected global error: {e}")
                break

        conn.close()
        print(f"\nSeed completed.")
        print(f"  Обработано вакансий: {total_processed}")
        print(f"  Найдено навыков всего: {total_skills_found}")
        return f"Database seeded with {total_processed} vacancies and {total_skills_found} skill relations"