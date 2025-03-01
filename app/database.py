from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import DATABASE_URL

# Create a database engine to connect to the PostgreSQL database
engine = create_engine(DATABASE_URL)

# Create a session factory to generate new database sessions
SessionLocal = sessionmaker(bind = engine, autocommit = False, autoflush = False)

# Base class for defining database models
Base = declarative_base()

def get_db():
    """
    Dependency function to provide a database session.

    Yields:
        Session: A database session instance.

    Ensures:
        - The session is properly closed after usage.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
