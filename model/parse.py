from selenium.webdriver.common.by import By
from selenium import webdriver
import psycopg2
from fastapi import FastAPI
from model.db import get_db_connection

app = FastAPI()

class SeedDatabase:
    @classmethod
    def seed(nothing):
        driver = webdriver.Chrome()
        driver.get("https://vladivostok.hh.ru/search/vacancy?area=22&L_save_area=true&search_field=name&search_field=company_name&search_field=description&enable_snippets=false&excluded_text=%D0%B3%D1%80%D0%B0%D0%B2%D0%B8%D1%80%D0%BE%D0%B2%D1%89%D0%B8%D0%BA%2C+%D1%84%D0%BB%D0%BE%D1%80%D0%B8%D1%81%D1%82&professional_role=25&professional_role=34&professional_role=96&professional_role=104&professional_role=116&professional_role=68&professional_role=170&professional_role=2&professional_role=73&professional_role=3&professional_role=103&professional_role=98")

        vacancies = driver.find_elements(By.CLASS_NAME, "vacancy-info--ieHKDTkezpEj0Gsx")

        # debug
        # print(f"Found {len(vacancies)} vacancies on the page")

        conn = get_db_connection()
        cur = conn.cursor()
        conn.autocommit = False

        cur.execute(
            """
            truncate table vacancyskills cascade;
            truncate table skills cascade;
            truncate table vacancies cascade;
            """
        )

        for vacancy in vacancies:
            title_elem = vacancy.find_element(By.CLASS_NAME, "bloko-header-section-2")
            title = title_elem.text.strip()
            employer = vacancy.find_element(By.CLASS_NAME, "company-name-badges-container--ofqQHaTYRFg0JM18").text.strip()
            experience = vacancy.find_element(By.CLASS_NAME, "magritte-tag__label___YHV-o_5-1-1").text.strip()
            link = title_elem.find_element(By.TAG_NAME, "a").get_attribute("href")

            # debug
            # print(f"Processing: {title[:60]}... | {employer} | Exp: {experience}")

            insert_vacancies = """
            insert into vacancies (title, employer, experience, url)
            values (%s, %s, %s, %s)
            returning vacancy_id;
            """

            insert_vacancyskills = """
            insert into vacancyskills (vacancy_id, skill_id)
            values (%s, %s);
            """

            try:
                cur.execute(insert_vacancies, (title, employer, experience, link))
                vacancy_id = cur.fetchone()[0]

                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[1])
                driver.get(link)

                skill_elements = driver.find_elements(By.CLASS_NAME, 'magritte-tag__label___YHV-o_5-1-1')
                for el in skill_elements:
                    txt = el.text.strip()
                    if not txt:
                        continue

                    cur.execute("""
                        INSERT INTO skills (title, skill_role)
                        VALUES (%s, %s)
                        ON CONFLICT (title) DO NOTHING
                        RETURNING skill_id;
                    """, (txt, 1))

                    row = cur.fetchone()
                    if row:
                        skill_id = row[0]
                    else:
                        cur.execute("SELECT skill_id FROM skills WHERE title = %s", (txt,))
                        skill_id = cur.fetchone()[0]

                    cur.execute(insert_vacancyskills, (vacancy_id, skill_id))

                driver.close()
                driver.switch_to.window(driver.window_handles[0])

                conn.commit()

                # debug
                # print("proceed") 

            except Exception as e:
                conn.rollback()
                print(f"ERROR: {e}")
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

        driver.quit()
        conn.close()

        return "nothing"