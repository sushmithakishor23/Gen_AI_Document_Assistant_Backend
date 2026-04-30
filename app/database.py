"""
Database Configuration
SQLAlchemy setup for metadata storage.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Create database directory
DB_DIR = Path("./data/db")
DB_DIR.mkdir(parents=True, exist_ok=True)

# SQLite database URL
DATABASE_URL = f"sqlite:///{DB_DIR}/documents.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session.
    Yields a session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Should be called at application startup.
    """
    from app.models import Collection, Document  # Import models
    Base.metadata.create_all(bind=engine)
    print(f"✓ Database initialized at {DATABASE_URL}")
