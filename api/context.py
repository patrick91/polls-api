from psycopg_pool import AsyncConnectionPool
from typing import TypedDict
from fastapi import Request

from .database import pool


class Context(TypedDict):
    request: Request
    pool: AsyncConnectionPool


async def context_getter(request: Request) -> Context:
    return {"request": request, "pool": pool}
