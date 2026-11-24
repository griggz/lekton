"""The thought: the one kind with no parent.

Every other kind is a thought plus something. Choosing the thought for
this place is an opinion, not a law.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any, ClassVar, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .relations import Composition, Requirement


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid4().hex


class Record(BaseModel):
    """Facts about a claim. Nobody has to agree with the claim to agree on these."""

    author: str
    recorded_at: datetime = Field(default_factory=_now)
    captured_from: str | None = None  # the call, doc, or session it came out of
    version: int = 1


class About(BaseModel):
    """One thing a claim touches. The role is set only when there is an assertion."""

    thing: str
    role: Literal["subject", "object"] | None = None


class Assertion(BaseModel):
    """The body reduced to one statement someone can agree or disagree with.

    The subject and object are not repeated here. They are marked as roles
    on the claim's `about` list, so the two cannot disagree.

    `modality` is the speaker's footing: they are telling you it is so
    (asserted), guessing (hypothesis), predicting (forecast), or passing
    on someone else's word (reported). It defaults to `unstated`, so a
    claim nobody examined never passes as a firm one.

    `basis` is how the modality is known: the speaker's own words carried
    it (stated), or whoever recorded the claim read it in (inferred).
    """

    predicate: str
    value: str | None = None  # the object, when it is not a thing
    polarity: Literal["+", "-"] = "+"
    modality: Literal["asserted", "hypothesis", "forecast", "reported", "unstated"] = "unstated"
    basis: Literal["stated", "inferred"] | None = None
    valid_at: date | None = None  # when the content holds; part of what is claimed

    @model_validator(mode="after")
    def _unstated_has_no_basis(self) -> Assertion:
        if self.modality == "unstated" and self.basis is not None:
            raise ValueError("an unstated modality has no basis: there is nothing to have a basis for")
        return self


class Ref(BaseModel):
    """A pointer to another claim, pinned to the version it was read at."""

    id: str
    version: int
    graph: str | None = None  # set when the claim lives in someone else's graph


class Link(BaseModel):
    """An edge from this claim to another: resolves, composed_of, evolved_from, supersedes."""

    verb: str
    to: Ref


class Thought(BaseModel):
    """The primitive. Subclass it to specialize: a subclass adds fields and never removes any."""

    # extra="allow" is what lets a graph read a kind it has never seen: the
    # fields it does not know ride along instead of being dropped.
    # ignored_types lets a kind declare its parts and required edges as
    # plain class attributes.
    model_config = ConfigDict(
        extra="allow",
        ignored_types=(Composition, Requirement),
    )

    id: str = Field(default_factory=_new_id)
    record: Record
    body: str = Field(min_length=1)  # what was said, verbatim
    about: list[About] = Field(min_length=1)  # everything it touches; at least one
    assertion: Assertion | None = None
    sourced_from: list[str] = Field(default_factory=list)  # evidence; can go stale
    links: list[Link] = Field(default_factory=list)

    # Set by load_kind when the kind's name does not come from a class name.
    __kind__: ClassVar[str | None] = None

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        # The parent rule: a kind adds to its parent and never redefines it.
        super().__pydantic_init_subclass__(**kwargs)
        parent = cls.parent()
        if parent is None:
            return
        own = set(cls.__dict__.get("__annotations__", {}))
        clashes = sorted(own & set(parent.model_fields))
        if clashes:
            raise TypeError(
                f"{cls.__name__} redefines {', '.join(clashes)}. "
                f"A kind adds fields to {parent.kind_name()}; it does not change the ones it inherits."
            )

    @field_validator("about", mode="before")
    @classmethod
    def _plain_strings_are_things(cls, value: Any) -> Any:
        # Lets callers write about=["traverse tool"] for the common case.
        if isinstance(value, list):
            return [{"thing": item} if isinstance(item, str) else item for item in value]
        return value

    @model_validator(mode="after")
    def _roles_need_an_assertion(self) -> Thought:
        if self.assertion is None and any(a.role for a in self.about):
            raise ValueError("a role on `about` only means something when there is an assertion")
        return self

    # --- the kind this class declares -------------------------------------

    @classmethod
    def kind_name(cls) -> str:
        """The kind's name: `Decision` is `decision`, `OpenQuestion` is `open_question`."""
        declared = cls.__dict__.get("__kind__")
        if declared:
            return declared
        return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()

    @classmethod
    def parent(cls) -> type[Thought] | None:
        """The kind this one specializes, or None for the thought itself."""
        for base in cls.__mro__[1:]:
            if isinstance(base, type) and issubclass(base, Thought):
                return base
        return None

    @classmethod
    def adds(cls) -> dict[str, Any]:
        """The fields this kind adds to its parent, by name."""
        parent = cls.parent()
        inherited = set(parent.model_fields) if parent else set()
        return {name: f for name, f in cls.model_fields.items() if name not in inherited}

    @classmethod
    def composition(cls) -> Composition | None:
        """What this kind is made of, if it is a composite. The nearest declaration wins."""
        for klass in cls.__mro__:
            for value in vars(klass).values():
                if isinstance(value, Composition):
                    return value
        return None

    @classmethod
    def requirements(cls) -> dict[str, type[Thought]]:
        """Required edges, verb to target kind. Inherited: a subclass never drops one."""
        found: dict[str, type[Thought]] = {}
        for klass in reversed(cls.__mro__):
            for value in vars(klass).values():
                if isinstance(value, Requirement):
                    found.update(value.edges)
        return found

    @classmethod
    def is_distinct(cls) -> bool:
        """Can this kind be told from its parent by structure alone?

        It can if it adds a required field or is made of parts. A kind that
        adds only optional fields has the same shape as its parent, so no
        structural check can pick it out.
        """
        if cls.parent() is None:
            return True
        if any(f.is_required() for f in cls.adds().values()):
            return True
        return any(isinstance(v, Composition) for v in vars(cls).values())

    # --- one claim ---------------------------------------------------------

    @property
    def kind(self) -> str:
        return type(self).kind_name()

    def ref(self) -> Ref:
        """A pointer to this claim at its current version."""
        return Ref(id=self.id, version=self.record.version)

    def with_link(self, verb: str, to: Thought | Ref) -> Thought:
        """A copy of this claim with one more edge. The original is left alone."""
        target = to.ref() if isinstance(to, Thought) else to
        return self.model_copy(update={"links": [*self.links, Link(verb=verb, to=target)]})

    def linked(self, verb: str) -> list[Ref]:
        """The targets of this claim's edges with the given verb."""
        return [link.to for link in self.links if link.verb == verb]
