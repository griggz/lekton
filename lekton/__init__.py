"""lekton: claim kinds built from one primitive.

A thought is the primitive. Every other kind is a thought plus something:
fields it adds (is-a), claims it is made of, each in a named role
(composed_of), or an edge it owes (requires).

    from lekton import Thought, Question, Decision
"""

from .check import Report, check, qualifies, read, resolved_by, status
from .declare import closure, declare, load_kind, load_kinds, to_yaml
from .kinds import Decision, Question
from .promote import promote
from .registry import kinds
from .relations import Role, composed_of, requires
from .thought import About, Assertion, Link, Record, Ref, Thought

__all__ = [
    "About",
    "Assertion",
    "Decision",
    "Link",
    "Question",
    "Record",
    "Ref",
    "Report",
    "Role",
    "Thought",
    "check",
    "closure",
    "composed_of",
    "declare",
    "kinds",
    "load_kind",
    "load_kinds",
    "promote",
    "qualifies",
    "read",
    "requires",
    "resolved_by",
    "status",
    "to_yaml",
]
