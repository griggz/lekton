"""The two relations a kind can declare besides is-a.

Is-a is subclassing. These are the other two:

    composed_of   the kind is made of other claims
    requires      the kind owes an edge to another claim

Both are declared as class attributes:

    class Bet(Thought):
        parts = composed_of(Decision, Risk)

    class Decision(Thought):
        needs = requires(resolves=Question)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .thought import Thought


class Composition:
    """What a composite kind is made of.

    parts    kinds it must contain, at least one claim of each
    allows   kinds a part may be; None means any claim
    min      fewest parts in total; a composite is two or more claims
    """

    def __init__(
        self,
        *parts: type[Thought],
        allows: list[type[Thought]] | None = None,
        min: int = 2,
    ) -> None:
        if min < 2:
            raise ValueError("a composite is made of two or more claims")
        self.parts = tuple(parts)
        self.allows = tuple(allows) if allows is not None else None
        self.min = max(min, len(self.parts))

    def __repr__(self) -> str:
        names = ", ".join(p.kind_name() for p in self.parts)
        return f"composed_of({names}, min={self.min})"


class Requirement:
    """Edges a kind owes, verb to target kind.

    A required edge is a completeness check, not a gate. A decision with
    no question is still a decision. It is an incomplete one.
    """

    def __init__(self, **edges: type[Thought]) -> None:
        self.edges = dict(edges)

    def __repr__(self) -> str:
        pairs = ", ".join(f"{verb}={kind.kind_name()}" for verb, kind in self.edges.items())
        return f"requires({pairs})"


def composed_of(
    *parts: type[Thought],
    allows: list[type[Thought]] | None = None,
    min: int = 2,
) -> Composition:
    """Declare that a kind is made of other claims."""
    return Composition(*parts, allows=allows, min=min)


def requires(**edges: type[Thought]) -> Requirement:
    """Declare an edge a kind owes. Keep these rare."""
    return Requirement(**edges)
