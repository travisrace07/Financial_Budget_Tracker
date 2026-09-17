"""Start the local dashboard using privately saved MySQL credentials."""
import json
from pathlib import Path
from sqlalchemy import URL
from app import create_app

if __name__ == '__main__':
    path = Path(__file__).with_name('.mysql-local.json')
    if not path.exists():
        raise SystemExit('First run: .venv/bin/python setup_mysql.py')
    config = json.loads(path.read_text())
    url = URL.create('mysql+pymysql', username=config['user'], password=config['password'], host=config['host'], port=config['port'], database=config['database'], query={'charset':'utf8mb4'})
    create_app(url).run(host='127.0.0.1', port=8001)
