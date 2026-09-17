"""Interactive local MySQL setup. Password input is never echoed."""
import getpass
import json
import os
from pathlib import Path
import secrets
import pymysql
from sqlalchemy import URL
from app import create_app

CONFIG = Path(__file__).with_name('.mysql-local.json')

def main():
    if CONFIG.exists():
        print('MySQL settings already exist. Run .venv/bin/python run_mysql.py')
        return
    print('Connect using the same MySQL administrator credentials as Workbench.')
    user = input('MySQL administrator username [root]: ').strip() or 'root'
    password = getpass.getpass('MySQL administrator password: ')
    app_password = secrets.token_urlsafe(32)
    # A unique account avoids changing an existing user or password.
    app_user = 'ledger_' + secrets.token_hex(4)
    connection = pymysql.connect(host='127.0.0.1', port=3306, user=user, password=password, autocommit=True)
    try:
        with connection.cursor() as cursor:
            cursor.execute('CREATE DATABASE IF NOT EXISTS ledger CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
            cursor.execute("CREATE USER %s@'localhost' IDENTIFIED BY %s", (app_user, app_password))
            cursor.execute("GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER ON ledger.* TO %s@'localhost'", (app_user,))
        config = dict(user=app_user, password=app_password, host='127.0.0.1', port=3306, database='ledger')
        url = URL.create('mysql+pymysql', username=app_user, password=app_password, host='127.0.0.1', port=3306, database='ledger', query={'charset':'utf8mb4'})
        create_app(url)  # Verify app access and create its tables before saving settings.
        fd = os.open(CONFIG, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as output:
            json.dump(config, output)
        print('\nConnected! Settings saved privately; your administrator password was not saved.')
        print('Start the dashboard: .venv/bin/python run_mysql.py')
        print('Then open http://127.0.0.1:8001')
    finally:
        connection.close()

if __name__ == '__main__':
    try:
        main()
    except (pymysql.MySQLError, OSError) as error:
        print(f'Setup could not complete: {error}')
        raise SystemExit(1)
