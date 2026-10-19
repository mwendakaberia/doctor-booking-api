
from sqlalchemy import text

from app.db.session import engine

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        print("Database connection successful!")
        print(result.scalar())
except Exception as exc:
    print("Database connection failed.")
    print(f"Error: {exc}")
