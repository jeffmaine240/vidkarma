# Connection Using SQLModel and Tenacity for retry logic

from tenacity import retry, stop_after_attempt, wait_fixed, RetryError
from sqlmodel import create_engine, text
from sqlalchemy.exc import OperationalError


from app.core.config import Config  # Import your configuration


DATABASE_URL = f"{Config.DB_TYPE}+psycopg2://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
engine = None  # Global placeholder


@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def connect_to_database():
    global engine
    try:
        engine = create_engine(
            DATABASE_URL,
            echo=False,               # Disable verbose SQL logging in prod
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
            future=True
        )
        
        # Force connection to verify success
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        print("Connected to the database.")
        return engine

    except OperationalError as oe:
        print(f"OperationalError: {oe}")
        raise oe
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise e


# Try to connect at module import time
try:
    connect_to_database()
except RetryError:
    print("Failed to connect to database after multiple attempts.")
    engine = None


