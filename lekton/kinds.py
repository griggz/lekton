"""The kinds that ship with the library. These are opinions about what a
question and a decision are; everything else is yours to define.
"""

from __future__ import annotations

from pydantic import Field

from .relations import composed_of, requires
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

    What was chosen is the decision's own body. Each alternative is a
    claim of its own, linked with `passed_over`, and so is the reason,
    linked with `because`. A decision adds no fields to a thought. What
    it adds is the roles other claims play around it.
    """

    parts = composed_of(passed_over=Thought)
    needs = requires(because=Thought, resolves=Question)
