"""The kinds that ship with the library. These are opinions about what a
question and a decision are; everything else is yours to define.
"""

from __future__ import annotations

from pydantic import Field

from .relations import requires
from .thought import Thought


class Question(Thought):
    """A thought that is waiting on an answer.

    There is no status field. A question is open until a claim that still
    stands resolves it (see `status`).
    """

    settled_by: str = Field(min_length=1)  # what would count as an answer
    owner: str | None = None  # who is expected to bring it


class Decision(Thought):
    """A thought that commits to one option over at least one other.

    The test: can you name what was chosen and one alternative passed over?
    """

    chosen: str = Field(min_length=1)  # identity: a different choice is a different decision
    alternatives: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1)

    needs = requires(resolves=Question)
