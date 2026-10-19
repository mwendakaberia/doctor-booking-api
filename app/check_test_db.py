import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

url = os.getenv("TEST_DATABASE_URL")

if not url:
    raise RuntimeError("TEST_DATABASE_URL is missing from .env")

engine = create_engine(url, pool_pre_ping=True)

with engine.connect() as connection:
    print(connection.execute(text("SELECT current_database()")).scalar())

engine.dispose()