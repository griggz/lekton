"""Turning a thought into something more specific.

Promotion is not an edit. It makes a new claim with its own record that
points back at the thought it came from.
"""

from __future__ import annotations

from typing import Any, TypeVar

from .thought import Link, Record, Thought

K = TypeVar("K", bound=Thought)


def promote(
    thought: Thought,
    kind: type[K],
    *,
    author: str | None = None,
    captured_from: str | None = None,
    **adds: Any,
) -> K:
    """Make a new claim of a more specific kind from an existing one.

    Pass the fields the kind adds as keyword arguments. Anything the
    thought already carries comes along; pass it again to override (a new
    `assertion`, for instance, when a hypothesis has become settled).

    Raises if the added fields do not satisfy the kind. Required edges are
    not checked here: run `check` on the result to see what it still owes.
    """
    if not issubclass(kind, type(thought)) or kind is type(thought):
        raise TypeError(
            f"cannot promote a {thought.kind} to a {kind.kind_name()}: "
            f"{kind.kind_name()} does not specialize {thought.kind}"
        )
    data = thought.model_dump(exclude={"id", "record", "links"})
    data.update(adds)
    data["record"] = Record(
        author=author or thought.record.author,
        captured_from=captured_from,
    )
    data["links"] = [Link(verb="evolved_from", to=thought.ref())]
    return kind.model_validate(data)
