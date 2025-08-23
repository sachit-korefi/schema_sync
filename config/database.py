from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from config import setting

DB_USER = setting.DB_USER
DB_PASSWORD = setting.DB_PASSWORD
DB_HOST = setting.DB_HOST
DB_PORT = setting.DB_PORT
DB_NAME = setting.DB_NAME
DB_SCHEMA = setting.SCHEMA_SYNC_DB_SCHEMA_NAME

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create a custom metadata with schema
metadata = MetaData(schema=DB_SCHEMA)

# Create base with the custom metadata
Base = declarative_base(metadata=metadata)

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
