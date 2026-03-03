import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from src.config.settings import settings
from src.data.clients.postgres import Base
from src.data.models.postgres.Appointment import Appointment
from src.data.models.postgres.AppointmentType import AppointmentType
from src.data.models.postgres.AvailabilitySlot import AvailabilitySlot
from src.data.models.postgres.Notification import Notification
from src.data.models.postgres.Patient import Patient
from src.data.models.postgres.Provider import Provider
from src.data.models.postgres.Role import Role
from src.data.models.postgres.Session import Session
from src.data.models.postgres.User import User

__all__ = [
    Appointment,
    AppointmentType,
    AvailabilitySlot,
    AvailabilitySlot,
    Notification,
    Patient,
    Provider,
    Role,
    Session,
    User,
]
config = context.config

DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{settings.POSTGRES_USERNAME}:"
    f"{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:"
    f"{settings.POSTGRES_PORT}/"
    f"{settings.POSTGRES_DB}"
)

config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
