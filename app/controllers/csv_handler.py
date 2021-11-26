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

@bp.route("/parsing/<file>/<pair>/<buyprice>/<sellprice>")
@bp.route("/parsing/<file>/<pair>")
@bp.route("/parsing/<file>")
def parsing_file(file, pair=None, buyprice=0, sellprice=0)-> str:
    table_name = file.split(".")[0]
    file = os.path.join(current_app.config['UPLOAD_FOLDER'], file)

    # step 1
    query = f'''
    select
        (select substring(date_time, 1, 8) from {table_name} 
         order by trade_id 
         limit 1) as first,
         (select substring(date_time, 1, 8) from {table_name} 
         order by trade_id desc
         limit 1) as last
    from {table_name}
    '''

    query1 = f'''
    select 
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

    query3 = f'''
    SELECT date_time, order_type, current_pair, quanity, price, order_value 
    FROM {table_name}
    WHERE current_pair LIKE '%RUB' 
    ORDER BY order_value DESC
    LIMIT 5
    '''

    query4 = f'''
    SELECT 
        (SELECT count(id) FROM {table_name} WHERE current_pair = '{pair}') AS total_deals,
        (SELECT count(id) 
            FROM {table_name} WHERE order_type = 'buy' 
            AND current_pair = '{pair}') as total_buy,
        (SELECT count(id) 
            FROM {table_name}
            WHERE order_type = 'sell' 
            AND current_pair = '{pair}') as total_sell,
        (SELECT count(id) 
            FROM {table_name} 
            WHERE order_type = 'buy' 
            AND current_pair = '{pair}'
            AND price = {buyprice}) as fixed_price_buy,
        (SELECT count(id) 
            FROM {table_name}
            WHERE order_type = 'sell' 
            AND current_pair = '{pair}'
            AND price = {sellprice}) as fixed_price_sell,
        (SELECT sum(order_value) 
            FROM {table_name}
            WHERE order_type = 'buy' 
            AND current_pair = '{pair}') as val_buy,
        (SELECT sum(order_value) 
            FROM {table_name}
            WHERE order_type = 'sell' 
            AND current_pair = '{pair}') as val_sell
    FROM {table_name}
    LIMIT 1
    '''

    total_stat = False
    top_pairs = False
    top_deals_rub = False
    pair_info = False
    # step 2
    order_date = None

    try:
        with mysql.connector.connect(**DBCONFIG) as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query1)
                total_stat = cursor.fetchone()

                cursor.execute(query2)
                top_pairs = cursor.fetchall()

                cursor.execute(query3)
                top_deals_rub = cursor.fetchall()

                if pair:
                    cursor.execute(query4)
                    pair_info = cursor.fetchone()
                    pair_info['pair_name'] = pair

                # step 3
                cursor.execute(query)
                order_date = cursor.fetchone()

    except mysql.connector.Error as e:
        print(e)

    # print('=====>', total_stat)
    # print('+++++>', top_pairs)
    # print('*****>', top_deals_rub)
    # print('/////>', pair_info)
    # print("@@@@>", order_date)

    if total_stat:
        return render_template("parsing_csv.html",
            table_name=table_name,
            stat=total_stat,
            top_pairs=top_pairs,
            top_deals_rub=top_deals_rub,
            pair_info=pair_info,
            price={
                "buy": buyprice,
                "sell": sellprice
            },
            # step 5
            order_date=order_date
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
