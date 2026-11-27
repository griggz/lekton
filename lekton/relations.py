"""The two relations a kind can declare besides is-a.

Is-a is subclassing. These are the other two:

    composed_of   the kind is made of other claims, each in a named role
    requires      the kind owes an edge to another claim

Both map a verb to a kind, and both are declared as class attributes:

    class Decision(Thought):
        parts = composed_of(passed_over=Thought)
        needs = requires(because=Thought, resolves=Question)

A role may ask for more than one claim. A pattern is seen in at least two:

    class Pattern(Thought):
        parts = composed_of(seen_in=(Thought, 2))

The verb is the edge on the claim. A decision's alternatives hang off it
as `passed_over` edges to claims of their own; its reason is a `because`
edge. The difference between the two relations is what a missing edge
means: without a part the claim is not this kind, without a required
edge it is this kind and owes one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .thought import Thought


class Role:
    """One role in a composite: the kind that fills it and how many it takes.

    `min` is the fewest claims of that kind the role needs. It is 1 unless
    the kind's meaning asks for more: a pattern recurs, so it is seen in at
    least two claims.
    """

    def __init__(self, kind: type[Thought], min: int = 1) -> None:
        if min < 1:
            raise ValueError("a role takes at least one claim")
        self.kind = kind
        self.min = min

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Role) and other.kind is self.kind and other.min == self.min

    def __hash__(self) -> int:
        return hash((self.kind, self.min))

    def __repr__(self) -> str:
        return f"{self.kind.kind_name()}" if self.min == 1 else f"({self.kind.kind_name()}, {self.min})"


RoleSpec = "type[Thought] | Role | tuple[type[Thought], int]"


def _role(spec: Any) -> Role:
    if isinstance(spec, Role):
        return spec
    if isinstance(spec, tuple):
        kind, min = spec
        return Role(kind, min)
    return Role(spec)


class Composition:
    """The parts a composite kind is made of, role to kind.

    Each role is a verb. A claim of this kind carries edges with that verb
    to at least `min` claims that fit the role's kind, one unless the role
    says otherwise. The parts stay as they are; the composite only points
    at them.
    """

    def __init__(self, **roles: Any) -> None:
        if not roles:
            raise ValueError("a composite names at least one role: composed_of(passed_over=Thought)")
        self.roles: dict[str, Role] = {verb: _role(spec) for verb, spec in roles.items()}

    def __repr__(self) -> str:
        pairs = ", ".join(f"{verb}={role!r}" for verb, role in self.roles.items())
        return f"composed_of({pairs})"


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


def composed_of(**roles: Any) -> Composition:
    """Declare the claims a kind is made of, by the role each one plays.

    A role is a kind, or `(kind, n)` for a role that takes at least n claims.
    """
    return Composition(**roles)


def requires(**edges: type[Thought]) -> Requirement:
    """Declare an edge a kind owes. Keep these rare."""
    return Requirement(**edges)
