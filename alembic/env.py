from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text, Table, Column, String, TIMESTAMP, func
from alembic import context
import os
import sys
from pathlib import Path
from alembic.script import ScriptDirectory


sys.path.append('.')
from config.database import Base
from config import setting
from config.logger import logger

# Explicitly import models to ensure they are registered with Base
from models.output_schema import OutputSchema
from models.user import User

target_metadata = Base.metadata


# Alembic Config
config = context.config
fileConfig(config.config_file_name)
# Build DB URL from env vars
DB_USER = setting.DB_USER
DB_PASSWORD = setting.DB_PASSWORD
DB_HOST = setting.DB_HOST
DB_PORT = setting.DB_PORT
DB_NAME = setting.DB_NAME
DB_SCHEMA = setting.SCHEMA_SYNC_DB_SCHEMA_NAME

logger.info(f"DB_USER: {DB_USER}")
logger.info(f"DB_PASSWORD: {DB_PASSWORD}")
logger.info(f"DB_HOST: {DB_HOST}")
logger.info(f"DB_PORT: {DB_PORT}")
logger.info(f"DB_NAME: {DB_NAME}")
logger.info(f"DB_SCHEMA: {DB_SCHEMA}")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    f"?options=-csearch_path={DB_SCHEMA}"
)




def get_next_number(versions_path):
    existing_files = list(Path(versions_path).glob("*.py"))
    numbers = []
    for f in existing_files:
        prefix = f.stem.split("_")[0]
        if prefix.isdigit():
            numbers.append(int(prefix))
    return max(numbers, default=0) + 1

def generate_migration_prefix(config, *args, **kwargs):
    # from alembic.script import ScriptDirectory
    script = ScriptDirectory.from_config(config)
    versions_path = script.versions
    next_number = get_next_number(versions_path)
    return f"{next_number:04d}"


# Define a custom alembic_version table
alembic_version = Table(
    "alembic_version",
    Base.metadata,
    Column("version_num", String(32), primary_key=True),
    Column(
        "applied_at",
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
    Column("model_name", String(255), server_default="unknown", nullable=False),
    schema=DB_SCHEMA,
)


def process_revision_directives(context, revision, directives):
    logger.info("Processing revision directives")
    if not directives:
        logger.warning("No directives found in process_revision_directives")
        return
    
    script = directives[0]
    logger.info(f"Script directives: {dir(script)}")
    
    # Log whether upgrade_ops exists and its content
    if hasattr(script, "upgrade_ops"):
        logger.info(f"Upgrade ops: {script.upgrade_ops}")
        logger.info(f"Is upgrade ops empty? {script.upgrade_ops.is_empty()}")
    
    # Do not skip empty revisions - always generate migration
    # Extract message (optional)
    message = getattr(script, "message", "manual")
    
    # Generate new revision ID
    script_dir = ScriptDirectory.from_config(context.config)
    prefix = generate_migration_prefix(context.config)
    old_revision_id = getattr(script, "rev_id", "base")
    new_revision_id = f"{prefix}_{old_revision_id}"
    
    # Update directive
    script.rev_id = new_revision_id
    new_filename = f"{new_revision_id}_{message}.py" if message else f"{new_revision_id}.py"
    script.path = os.path.join(script_dir.versions, new_filename)
    
    logger.info(f"Generated migration: {new_filename}")


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and object.schema != DB_SCHEMA:
        return False
    if name == "alembic_version":
        return False
    return True


def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": DATABASE_URL},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as conn:
        logger.info(f"Creating schema {DB_SCHEMA}")
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}"))

    with connectable.connect() as connection:
        logger.info(f"Running migrations on {DB_SCHEMA}")
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            version_table_schema=DB_SCHEMA,
            compare_type=True,
            process_revision_directives=process_revision_directives,
        )
        with context.begin_transaction():
            logger.info(f"Running creating tables on {DB_SCHEMA}")
            context.run_migrations()


run_migrations_online()
