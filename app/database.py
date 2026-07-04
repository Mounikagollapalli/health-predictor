"""
database.py
------------
Sets up the SQLite database engine and session for the application using
SQLAlchemy. The database file (health.db) is created automatically in the
project root the first time the app runs.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'health.db')}"

# check_same_thread=False is required for SQLite when used with FastAPI's
# threaded request handling.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session and ensures it is
    closed after the request completes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
