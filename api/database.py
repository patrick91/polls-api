import os

from psycopg_pool import AsyncNullConnectionPool

pool = AsyncNullConnectionPool(
    os.environ["DATABASE_URL"],
    open=False,
)
