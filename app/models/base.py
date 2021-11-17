import mysql.connector
import os
import csv

DBCONFIG = {
    "host": os.environ.get("DBHOST"),
    "user": os.environ.get("DBUSER"),
    "password": os.environ.get("DBPASSWORD"),
    "database": os.environ.get("DBNAME"),
    # "allow_local_infile": True,
}


def create_table(csv_filename):
    table_name = csv_filename.split(".")[0]

    query = """CREATE TABLE IF NOT EXISTS %s (
    id                INT(11) PRIMARY KEY AUTO_INCREMENT, 
    date_time         VARCHAR(18) NOT NULL,
    trade_id          BIGINT UNSIGNED NOT NULL,
    order_type        ENUM('buy', 'sell') NOT NULL,
    current_pair      VARCHAR(18) NOT NULL,
    quanity           DECIMAL(18,9) NOT NULL,
    price             DECIMAL(18,9) NOT NULL,
    order_value       DECIMAL(18,9) NOT NULL,
    comission_type    VARCHAR(10) NOT NULL,
    comission_value   DECIMAL(18,9) NOT NULL,
    comission_percent VARCHAR(10) NOT NULL
    );""" % table_name

    with mysql.connector.connect(**DBCONFIG) as connect:
        with connect.cursor() as cursor:
            cursor.execute(query)


def insert_from_csv(file, table_name):
    conn = mysql.connector.connect(**DBCONFIG)
    cursor = conn.cursor(prepared=True)

    with open(file, newline='') as File:
        reader = csv.reader(File)

        for row in reader:
            break
        for row in reader:
            query = """INSERT INTO %s (
            date_time, trade_id, order_type, current_pair, quanity,
            price, order_value, comission_type, comission_value, comission_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""" % table_name

            cursor.execute(query, tuple(row))

    conn.commit()
    cursor.close()
    conn.close()


def drop_table(table_name):
    with mysql.connector.connect(**DBCONFIG) as connect:
        with connect.cursor() as cursor:
            cursor.execute("""DROP TABLE %s;""" % table_name)
