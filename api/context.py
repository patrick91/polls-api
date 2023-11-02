from typing import TypedDict

from fastapi import Depends, Request
from psycopg_pool import AsyncConnectionPool

from .auth.verifier import BasicVerifier, verifier
from .database import pool


class Context(TypedDict):
    request: Request
    pool: AsyncConnectionPool
    verifier: BasicVerifier


async def context_getter(
    request: Request, verifier: BasicVerifier = Depends(verifier)
) -> Context:
    return {"request": request, "pool": pool, "verifier": verifier}
