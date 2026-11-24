"""Shared claims for the tests, built on a real pair: a thought about the
traverse tool, the question it raised, and the decision it became.
"""

from __future__ import annotations

import pytest

from lekton import Assertion, Decision, Question, Record, Thought, composed_of


class Risk(Thought):
    likelihood: str
    impact: str


class Bet(Thought):
    thesis: str
    parts = composed_of(Decision, Risk)


class Position(Thought):
    """Adds nothing required, so structure cannot tell it from a thought."""

    stance: str | None = None


@pytest.fixture
def thought() -> Thought:
    return Thought(
        record=Record(author="wayne", captured_from="working session"),
        body=(
            "I do not think I ever use the traverse tool, so losing it in "
            "a port is not a concern for me."
        ),
        about=[
            {"thing": "traverse tool", "role": "subject"},
            "Postgres port",
            "Cypher",
        ],
        # "I do not think": a guess, and the speaker's own words say so.
        assertion=Assertion(
            predicate="is never used by me", modality="hypothesis", basis="stated"
        ),
    )


@pytest.fixture
def question() -> Question:
    return Question(
        record=Record(author="wayne"),
        body="Does the traverse tool come along in the Postgres port?",
        about=["traverse tool", "Postgres port"],
        settled_by="A call on whether to port it, replace it, or retire it.",
    )


@pytest.fixture
def decision() -> Decision:
    return Decision(
        record=Record(author="wayne"),
        body="Retire the traverse tool in the Postgres port.",
        about=["traverse tool", "Postgres port"],
        chosen="Retire it, with no replacement",
        alternatives=["A read-only SQL tool with the same gating"],
        rationale="Unused, already off on shared instances, and it cannot be ported as is.",
    )


@pytest.fixture
def risk() -> Risk:
    return Risk(
        record=Record(author="wayne"),
        body="Someone depends on arbitrary Cypher and we have not heard from them.",
        about=["traverse tool"],
        likelihood="low",
        impact="one workflow breaks",
    )
