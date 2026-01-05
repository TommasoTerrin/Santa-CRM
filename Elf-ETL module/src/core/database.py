from sqlmodel import SQLModel, create_engine, Session
try:
    from .models import Child, Letter
except ImportError:
    from core.models import Child, Letter
from dotenv import load_dotenv
import os

load_dotenv()

SANTA_DB_URL = os.getenv("SANTA_DB_URL")

# Keep the connection string compatible if using postgres (docker) vs sqlite
# If 'postgres' in URL string but using psycopg2, it might need postgresql://
if SANTA_DB_URL and SANTA_DB_URL.startswith("postgres://"):
    SANTA_DB_URL = SANTA_DB_URL.replace("postgres://", "postgresql://", 1)

# Create engine
engine = create_engine(SANTA_DB_URL, echo=True)

def init_db():
    """Initializes the database by creating tables."""
    SQLModel.metadata.create_all(engine)

def reset_db():
    """Drops all tables and recreates them (Heavy Reset)."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency to get a DB session."""
    with Session(engine) as session:
        yield session
