from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from ...config.settings import settings

POOL_URL = (
    f"postgresql://{settings.POSTGRES_USERNAME}:"
    f"{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:"
    f"{settings.POSTGRES_PORT}/"
    f"{settings.POSTGRES_DB}"
)

checkpoint_pool = AsyncConnectionPool(
    conninfo=POOL_URL,
    max_size=10,
    kwargs={"autocommit": True},
    open=False,
)

checkpointer = AsyncPostgresSaver(checkpoint_pool)
