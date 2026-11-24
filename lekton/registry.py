"""Every kind the process knows about, by name."""

from __future__ import annotations

from .thought import Thought


def kinds() -> dict[str, type[Thought]]:
    """All defined kinds, the thought first. A later kind with the same name wins."""
    found: dict[str, type[Thought]] = {Thought.kind_name(): Thought}
    queue: list[type[Thought]] = [Thought]
    while queue:
        for sub in queue.pop(0).__subclasses__():
            found[sub.kind_name()] = sub
            queue.append(sub)
    return found
