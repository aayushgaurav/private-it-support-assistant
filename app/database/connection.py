from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Project root directory
PROJECT_DIR = Path(__file__).resolve().parents[2]

# SQLite database location
DATABASE_PATH = PROJECT_DIR / "data" / "users.db"

# Database connection URL
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for database models
Base = declarative_base()

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()