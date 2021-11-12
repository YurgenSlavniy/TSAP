# TSAP

### Виртуальное окружение
+ python3.x -m venv venv | py -3 -m venv venv

### Активировать
+ source ./venv/bin/activate | venv\Scripts\activate

### Зависимости
+ pip|pip3 install requirements.txt

### Переменные перед запуском приложения
+ bash 	   export FLASK_
+ cmd 	   set FLASK_
+ PowerShell $env:FLASK_

+ FLASK_ENV=development
+ DBNAME=
+ DBHOST=
+ DBUSER=
+ DBPASSWORD=

### Или создать файл .env, будет все автоматически, пример в .env.example

##### Запустить приложение

flask run
