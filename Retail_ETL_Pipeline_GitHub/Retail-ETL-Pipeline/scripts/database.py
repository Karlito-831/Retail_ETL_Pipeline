"""Database connection shared by the proposed-artifact Flask application."""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

def get_engine():
    keys = ('DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME')
    missing = [key for key in keys if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            'Missing database configuration: ' + ', '.join(missing)
            + '. Copy .env.example to .env in the project folder and enter your existing PostgreSQL credentials.'
        )
    # URL.create handles special characters in passwords safely.
    url = URL.create(
        'postgresql+psycopg2',
        username=os.environ['DB_USER'], password=os.environ['DB_PASSWORD'],
        host=os.environ['DB_HOST'], port=int(os.environ['DB_PORT']),
        database=os.environ['DB_NAME'],
    )
    return create_engine(url, pool_pre_ping=True)
