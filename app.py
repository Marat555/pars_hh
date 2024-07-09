import mysql.connector
import requests
from mysql.connector import Error
from flask import Flask, request, render_template
from flask_paginate import Pagination, get_page_parameter

app = Flask(__name__)


def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port='3306',
            user='user',
            password='54162004Mmarat!',
            database='pars_hh'
        )
        if connection.is_connected():
            db_Info = connection.get_server_info()
            print("Подключено к MySQL серверу версии ", db_Info)
            cursor = connection.cursor()
            cursor.execute("select database();")
            record = cursor.fetchone()
            print("Вы подключены к базе данных: ", record)
            return connection
    except Error as e:
        print("Ошибка при подключении к MySQL", e)
        return None


def get_vacancies(keyword, fio, position, skills, work_format, page=1, per_page=20):
    url = "https://api.hh.ru/vacancies"
    params = {
        "text": keyword,
        "area": 1,
        "per_page": per_page,
        "page": page - 1,
    }
    headers = {
        "User-Agent": "Your User Agent",
        "Authorization": "Bearer USERSO38M6BSF7E6VVOOA2HHNLHQ0F81IE5STG4H4D18OVRJMCFCD0J64QIHMVF2"

    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()
        vacancies = data.get("items", [])
        num_vacancies = len(vacancies)

        if num_vacancies > 0:
            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("DELETE FROM vacancies")
                    connection.commit()
                    for vacancy in vacancies:
                        vacancy_id = vacancy.get("id")
                        vacancy_title = vacancy.get("name")
                        vacancy_url = vacancy.get("alternate_url")
                        company_name = vacancy.get("employer", {}).get("name")
                        insert_query = """INSERT INTO vacancies (vacancy_id, vacancy_title, company_name, vacancy_url, fio, position, skills, work_format)
                                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                        record = (
                            vacancy_id, vacancy_title, company_name, vacancy_url, fio, position, skills, work_format)
                        cursor.execute(insert_query, record)
                        connection.commit()
                        print(f"Вакансия {vacancy_id} успешно добавлена в таблицу vacancies")
                except Error as e:
                    print(f"Ошибка при вставке данных в MySQL: {e}")
                finally:
                    cursor.close()
                    connection.close()
            else:
                print("Не удалось установить соединение с базой данных")
    else:
        print(f"Запрос завершился с кодом состояния: {response.status_code}")


@app.route('/', methods=['GET'])
def home():
    return render_template('search.html')


@app.route('/search', methods=['POST'])
def search_vacancies():
    keyword = request.form['keyword']
    fio = request.form['fio']
    position = request.form['position']
    skills = request.form['skills']
    work_format = request.form['work_format']
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 10

    get_vacancies(keyword, fio, position, skills, work_format, page, per_page)
    return render_template('search_results.html')


@app.route('/vacancies', methods=['GET'])
def list_vacancies():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 10
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT vacancy_title, company_name, vacancy_url FROM vacancies LIMIT %s OFFSET %s", (per_page, (page - 1) * per_page))
        vacancies = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM vacancies")
        total = cursor.fetchone()[0]
        cursor.close()
        connection.close()

        pagination = Pagination(page=page, total=total, per_page=per_page, css_framework='bootstrap4')
        return render_template('vacancies.html', vacancies=vacancies, pagination=pagination)
    else:
        return "Ошибка подключения к базе данных"


@app.route('/analytics')
def analytics():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM vacancies")
        total_vacancies = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM candidates")
        total_candidates = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return render_template('analytics.html', total_vacancies=total_vacancies, total_candidates=total_candidates)
    else:
        return "Ошибка подключения к базе данных"


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
