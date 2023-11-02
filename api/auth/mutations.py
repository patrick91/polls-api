from typing import Any
from uuid import uuid4

import strawberry
from fastapi_sessions.frontends.implementations import (  # type: ignore
    CookieParameters,
    SessionCookie,
)
from strawberry.types.info import Info

from .verifier import SessionData, backend

cookie_params = CookieParameters()

cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",
    cookie_params=cookie_params,
)


@strawberry.type
class LoginResponse:
    message: str


@strawberry.type
class AuthQuery:
    @strawberry.field
    async def me(self, info: Info[Any, None]) -> str:
        print(info.context["request"].session)
        return "test"


@strawberry.type
class AuthMutation:
    @strawberry.mutation
    async def login(
        self,
        info: Info[Any, None],
        username: str,
        password: str,
    ) -> LoginResponse:
        print(username, password, info)

        session = uuid4()
        data = SessionData(username=username)

        response = info.context["response"]

        await backend.create(session, data)
        cookie.attach_to_response(response, session)
        return LoginResponse(message="Logged in successfully")
