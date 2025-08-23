import os
from dotenv import load_dotenv

# Load env vars from .env file
load_dotenv()


# Database
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres1")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_PORT = os.getenv("DB_PORT", 5432)
SCHEMA_SYNC_DB_SCHEMA_NAME = os.getenv("SCHEMA_SYNC_DB_SCHEMA_NAME", "ç").lower()