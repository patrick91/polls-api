import strawberry
from typing import Any
from strawberry.types.info import Info

from strawberry.directive import DirectiveLocation

from .context import Context

# TODO: use dataloaders


@strawberry.type
class Answer:
    id: strawberry.ID
    text: str
    votes: int
    percentage: float


@strawberry.type
class Poll:
    id: strawberry.ID
    question: str

    @strawberry.field
    async def answers(self, info: Info[Context, None]) -> list[Answer]:
        pool = info.context["pool"]

        async with pool.connection() as db:
            cur = await db.execute(
                """
                SELECT a.id, a.text, COALESCE(v.vote_count, 0) AS vote_count
                FROM answers a
                LEFT JOIN (
                    SELECT answer_id, COUNT(*) AS vote_count
                    FROM votes
                    GROUP BY answer_id
                ) v ON a.id = v.answer_id
                WHERE a.poll_id = %s
                """,
                (self.id,),
            )

            results = await cur.fetchall()

            answers = [
                Answer(
                    id=answer_id,
                    text=text,
                    votes=votes,
                    percentage=0,
                )
                for answer_id, text, votes in results
            ]

        total_votes = sum(answer.votes for answer in answers)

        if total_votes > 0:
            for answer in answers:
                answer.percentage = (answer.votes / total_votes) * 100

        return answers

    @strawberry.field
    async def total_votes(self, info: Info[Context, None]) -> int:
        pool = info.context["pool"]

        async with pool.connection() as db:
            cur = await db.execute(
                """
                SELECT COUNT(*) AS total_votes
                FROM votes v
                JOIN answers a ON v.answer_id = a.id
                WHERE a.poll_id = %s
                """,
                (self.id,),
            )

            result = await cur.fetchone()

            return 0 if result is None else result[0]


@strawberry.type
class Query:
    @strawberry.field
    async def poll(self, info: Info[Context, None], id: strawberry.ID) -> Poll | None:
        pool = info.context["pool"]

        async with pool.connection() as db:
            cur = await db.execute("SELECT question FROM polls WHERE id = %s", (id,))

            result = await cur.fetchone()

            return None if result is None else Poll(id=id, question=result[0])


@strawberry.type
class Mutation:
    @strawberry.field
    async def answer_poll(
        self, id: strawberry.ID, answer_id: strawberry.ID, info: Info[Context, None]
    ) -> Poll | None:
        pool = info.context["pool"]

        async with pool.connection() as db:
            cur = await db.execute("SELECT question FROM polls WHERE id = %s", (id,))

            question = await cur.fetchone()

            if question is None:
                return None

            cur = await db.execute(
                "SELECT id FROM answers WHERE id = %s AND poll_id = %s", (answer_id, id)
            )

            result = await cur.fetchone()

            if result is None:
                return None

            cur = await db.execute(
                "INSERT INTO votes (answer_id) VALUES (%s)",
                (answer_id,),
            )

            await db.commit()

            return Poll(id=id, question=question[0])


# a directive that adds some delay to a resolver
@strawberry.directive(
    description="Adds a delay to the resolver, useful for testing loading states",
    locations=[DirectiveLocation.FIELD],
)
async def delay(
    value: Any,
    ms: int = 1000,
) -> Any:
    import asyncio

    # sourcery skip: remove-unnecessary-cast
    # this is due to a bug in Strawberry
    await asyncio.sleep(int(ms) / 1000)

    return value


schema = strawberry.federation.Schema(
    Query,
    Mutation,
    enable_federation_2=True,
    directives=[delay],
)
