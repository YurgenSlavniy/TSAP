from werkzeug.utils import secure_filename
from flask import (
    Blueprint, render_template, request, current_app, flash, redirect, url_for,
    send_from_directory
)
from app.models.base import DBCONFIG, create_table, insert_from_csv, drop_table
#
import os
import uuid
import mysql.connector

bp = Blueprint("csv_handler", __name__)


@bp.route("/csv/file/uploads/page")
def show_load_page()-> str:
    '''Показывает страницу загрузки файла'''
    return render_template("load_csv.html")


def allowed_file(filename)-> bool:
    '''определяет имеет ли файл расширение .csv'''
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {"csv"}


@bp.route("/upload/csv/file", methods=['GET', 'POST'])
def upload_file()-> None:
    '''Загрузка файла csv в ../uploads'''
    if request.method == "POST":

        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(url_for("csv_handler.show_load_page"))
        file = request.files['file']

        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == "":
            flash('Не выбран файл.')
            return redirect(url_for("csv_handler.show_load_page"))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Новое имя csv файла сгенерированное случайным образом
            new_filename = "_".join(str(uuid.uuid4()).split("-")) + ".csv"

            file.save(os.path.join(
                current_app.config['UPLOAD_FOLDER'], new_filename))

            # Создаем таблицу с таким же именем как имя файла но без расширения .csv
            # такого вида 86b2af33_6937_418a_8e9b_b9dfdb766514
            # Таблица создается даже если формат данных не корректен
            create_table(new_filename)

            # Если произойдет ошибка при вставке в таблицу.
            # Ошибка должна происходить, если формат файла не корректен
            # Удаляем сгенерированную таблицу и сам файл csv
            try:
                table_name = new_filename.split(".")[0]
                upload_file = os.path.join(
                    current_app.config['UPLOAD_FOLDER'], new_filename)

                insert_from_csv(upload_file, table_name)
                flash("Файл загружен.")
                flash("Таблица создана.")
            except mysql.connector.Error as e:
                os.remove(upload_file)
                drop_table(table_name)
                flash("Формат данных файла был не корректен!")
                return redirect(url_for("csv_handler.show_load_page"))

            return redirect(url_for("csv_handler.parsing_file", file=new_filename))

    flash("Формат файла должен иметь расширение .csv")
    return redirect(url_for("csv_handler.show_load_page"))


@bp.route("/parsing/<file>")
def parsing_file(file)-> str:
    table_name = file.split(".")[0]
    file = os.path.join(current_app.config['UPLOAD_FOLDER'], file)

    query1 = f'''
    select id, 
        (select count(id) from {table_name}) as total,
        (select count(id) from {table_name} where order_type = 'buy') as total_buy,
        (select count(id) from {table_name} where order_type = 'sell') as total_sell,
        (select count(distinct current_pair) from {table_name}) as total_pair
    from {table_name}
    limit 1
    '''

    query2 = f'''
    SELECT count(*) AS total, current_pair  FROM {table_name} 
    GROUP BY current_pair
    ORDER BY total DESC
    LIMIT 5
    '''
    row = False
    top_pairs = False
    try:
        with mysql.connector.connect(**DBCONFIG) as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query1)
                row = cursor.fetchone()

                cursor.execute(query2)
                top_pairs = cursor.fetchall()

    except mysql.connector.Error as e:
        print(e)

    print('====>', row)
    print('+++++>', top_pairs)

    if row:
        return render_template(
            "parsing_csv.html",
            drop_name=table_name,
            stat=row, top_pairs=top_pairs
        )
    else:
        flash("Данные отсутствуют")
        return render_template("parsing_csv.html")


@bp.route("/drop/<table>")
def drop(table):
    # Код ниже добавлен временно для примера
    # Если произойдет ошибка, ошибка происходит если таблица была удалена
    # Пока гнорируем ее, потом видно будет
    try:
        drop_table(table)
        os.remove(os.path.join(
            current_app.config['UPLOAD_FOLDER'], table+".csv"))
        flash("Таблица и файл удалены")
    except mysql.connector.Error as e:
        pass

    return redirect(url_for("csv_handler.parsing_file", file=table+".csv"))
