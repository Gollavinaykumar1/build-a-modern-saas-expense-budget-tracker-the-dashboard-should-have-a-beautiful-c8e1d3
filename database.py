# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
# Using a local PostgreSQL database for demonstration
# Replace with your actual database URL, e.g., for production
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/expense_tracker_db")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# You would typically use Alembic for migrations,
# but for a quick start, we'll create tables directly.
def create_tables():
    """Creates all defined tables in the database."""
    Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    # This block can be used to manually create tables if not using Alembic
    print("Attempting to create database tables...")
    create_tables()
    print("Database tables created (if they didn't exist).")