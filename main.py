from http import HTTPStatus
from os import environ
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from api.context import Context, context_getter
from api.database import pool
from api.schema import schema

app = FastAPI()

allow_origin_regex = r"^(https://.*\.vercel\.app)|(https://studio\.apollographql\.com)|(http://localhost:3000)$"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


graphql_app = GraphQLRouter[Context, None](
    schema, path="/", context_getter=context_getter
)

app.include_router(graphql_app)


@app.middleware("http")
async def check_router_security(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    router_secret = environ.get("ROUTER_SECRET")
    if router_secret is None:
        return await call_next(request)
    if request.headers.get("Router-Authorization") != router_secret:
        return Response(status_code=HTTPStatus.UNAUTHORIZED)
    return await call_next(request)


@app.on_event("startup")
async def open_pool():
    await pool.open()


@app.on_event("shutdown")
async def close_pool():
    await pool.close()
