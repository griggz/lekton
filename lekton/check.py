"""Deciding what a claim is by its structure, not its label.

`check` is the authority. A class name or a `kind` key is a label, and a
label can be wrong. `check` looks at what the claim actually carries.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from .registry import kinds as all_kinds
from .thought import Link, Ref, Thought

Claim = Thought | Mapping[str, Any]


@dataclass(frozen=True)
class Report:
    """What `check` found.

    missing      fields or parts the claim lacks; without them it is not this kind
    owed         required edges not yet in place; it is this kind, but incomplete
    unverified   edges that exist but point at claims that could not be looked up
    revised      linked claims that have a newer version than the one pinned
    detail       the reason behind each `missing` entry
    """

    kind: str
    missing: tuple[str, ...] = ()
    owed: tuple[str, ...] = ()
    unverified: tuple[str, ...] = ()
    revised: tuple[str, ...] = ()
    detail: Mapping[str, str] = field(default_factory=dict)

    @property
    def fits(self) -> bool:
        """Is the claim this kind?"""
        return not self.missing

    @property
    def complete(self) -> bool:
        """Is it this kind with every required edge in place and looked up?"""
        return self.fits and not self.owed and not self.unverified


def _data(claim: Claim) -> dict[str, Any]:
    data = claim.model_dump() if isinstance(claim, Thought) else dict(claim)
    data.pop("kind", None)  # a label; structure decides
    return data


def _index(known: Iterable[Thought] | Mapping[str, Thought]) -> dict[str, Thought]:
    if isinstance(known, Mapping):
        return dict(known)
    return {claim.id: claim for claim in known}


def _links(data: Mapping[str, Any]) -> list[Link]:
    links = []
    for raw in data.get("links") or []:
        try:
            links.append(raw if isinstance(raw, Link) else Link.model_validate(raw))
        except ValidationError:
            continue
    return links


def _empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def check(
    claim: Claim,
    kind: type[Thought] | None = None,
    *,
    known: Iterable[Thought] | Mapping[str, Thought] = (),
) -> Report:
    """Check a claim against a kind. Never raises on a claim that falls short.

    `kind` defaults to the claim's own class, or the thought for plain data.
    `known` is the set of claims that edges can be looked up in.
    """
    if kind is None:
        kind = type(claim) if isinstance(claim, Thought) else Thought
    data = _data(claim)
    index = _index(known)
    missing: list[str] = []
    detail: dict[str, str] = {}

    def lacks(name: str, why: str) -> None:
        if name not in missing:
            missing.append(name)
            detail[name] = why

    # Fields. Pydantic is the judge of shape.
    try:
        kind.model_validate(data)
    except ValidationError as error:
        for problem in error.errors():
            name = str(problem["loc"][0]) if problem["loc"] else "claim"
            lacks(name, problem["msg"])
    # Required means present and not empty, whether or not the class says so.
    for name, info in kind.model_fields.items():
        if info.is_required() and _empty(data.get(name)):
            lacks(name, "required and empty")

    links = _links(data)
    unverified: list[str] = []
    revised: list[str] = []

    def targets(verb: str) -> tuple[list[Thought], int]:
        """The claims a verb points at that could be looked up, and how many could not."""
        found, lost = [], 0
        for link in links:
            if link.verb != verb:
                continue
            target = index.get(link.to.id)
            if target is None:
                lost += 1
                continue
            found.append(target)
            if target.record.version > link.to.version:
                revised.append(
                    f"{verb}: {target.id} pinned at v{link.to.version}, now v{target.record.version}"
                )
        return found, lost

    # Parts. A composite without its parts is not that composite.
    composition = kind.composition()
    if composition is not None:
        found, lost = targets("composed_of")
        if len(found) + lost < composition.min:
            lacks("composed_of", f"needs {composition.min} parts, has {len(found) + lost}")
        for part in composition.parts:
            if any(check(t, part, known=index).fits for t in found):
                continue
            if lost:
                unverified.append(f"composed_of: {part.kind_name()}")
            else:
                lacks(f"composed_of: {part.kind_name()}", "no part of this kind")
        if composition.allows is not None:
            for target in found:
                if not any(check(target, ok, known=index).fits for ok in composition.allows):
                    lacks(f"composed_of: {target.id}", f"a {target.kind} is not an allowed part")

    # Required edges. Owed, not disqualifying.
    owed: list[str] = []
    for verb, wanted in kind.requirements().items():
        label = f"{verb}: {wanted.kind_name()}"
        found, lost = targets(verb)
        if any(check(t, wanted, known=index).fits for t in found):
            continue
        if lost:
            unverified.append(label)
        else:
            owed.append(label)

    return Report(
        kind=kind.kind_name(),
        missing=tuple(missing),
        owed=tuple(owed),
        unverified=tuple(unverified),
        revised=tuple(dict.fromkeys(revised)),
        detail=detail,
    )


def qualifies(
    claim: Claim,
    *,
    kinds: Iterable[type[Thought]] | None = None,
    known: Iterable[Thought] | Mapping[str, Thought] = (),
) -> list[type[Thought]]:
    """The most specific kinds a claim's structure fits.

    Empty if it is not even a thought. Kinds that cannot be told from
    their parent by structure (see `Thought.is_distinct`) are skipped.
    """
    pool = list(kinds) if kinds is not None else list(all_kinds().values())
    index = _index(known)
    fitting = [k for k in pool if k.is_distinct() and check(claim, k, known=index).fits]
    return [k for k in fitting if not any(o is not k and issubclass(o, k) for o in fitting)]


def read(
    data: Claim,
    *,
    kinds: Iterable[type[Thought]] | None = None,
    known: Iterable[Thought] | Mapping[str, Thought] = (),
) -> Thought:
    """Build a claim as the most specific known kind its structure fits.

    A kind this process has never seen comes back as its nearest known
    ancestor with its extra fields intact. Raises if the data is not a thought.
    """
    payload = _data(data)
    best = qualifies(payload, kinds=kinds, known=known)
    if not best:
        return Thought.model_validate(payload)  # raises, saying why
    if len(best) == 1:
        return best[0].model_validate(payload)
    # It fits unrelated kinds at once. Fall back to what they share.
    for shared in best[0].__mro__:
        if issubclass(shared, Thought) and all(issubclass(k, shared) for k in best):
            return shared.model_validate(payload)
    return Thought.model_validate(payload)


def resolved_by(question: Thought, known: Iterable[Thought]) -> list[Thought]:
    """The claims that resolve a question and still stand.

    A claim stands until another claim supersedes it.
    """
    pool = list(known)
    superseded = {ref.id for claim in pool for ref in claim.linked("supersedes")}
    return [
        claim
        for claim in pool
        if claim.id not in superseded
        and any(ref.id == question.id for ref in claim.linked("resolves"))
    ]


def status(question: Thought, known: Iterable[Thought]) -> str:
    """`open` or `answered`. Worked out from edges every time; never stored."""
    return "answered" if resolved_by(question, known) else "open"


__all__ = ["Claim", "Ref", "Report", "check", "qualifies", "read", "resolved_by", "status"]
