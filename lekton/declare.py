"""Kinds as data.

`declare` writes a kind out in the template format. `load_kind` reads the
format back and builds the kind at runtime, with no code written. This is
what lets a kind be shared between graphs.

The format, on a question and a decision:

    question:
      specializes: thought
      adds:
        settled_by: text
        owner: text?

    decision:
      specializes: thought
      parts:
        passed_over: thought
      requires:
        because: thought
        resolves: question

`parts` and `requires` both map a verb to a kind. A part is constitutive:
without one the claim is not this kind. A required edge is owed. A part
that takes more than one claim says so:

    pattern:
      specializes: thought
      parts:
        seen_in: {kind: thought, min: 2}

Types: text, integer, number, boolean, date, datetime, a list `[text]`,
or a choice `open|won|lost`. A trailing `?` marks a field optional, on
the type for plain values (`text?`) and on the name for lists (`tags?:`).
A required text or list field must not be empty.
"""

from __future__ import annotations

import types
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any, Literal, Union, get_args, get_origin

import yaml
from pydantic import BaseModel, Field, create_model

from .registry import kinds as all_kinds
from .relations import Composition, Requirement, Role
from .thought import Thought

_NAMES: dict[type, str] = {
    str: "text",
    int: "integer",
    float: "number",
    bool: "boolean",
    date: "date",
    datetime: "datetime",
}
_TYPES: dict[str, type] = {name: py for py, name in _NAMES.items()}


# --- writing a kind out -----------------------------------------------------


def _spell(annotation: Any) -> tuple[Any, bool]:
    """An annotation in the template's words, and whether it allows None."""
    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):
        inner = [a for a in get_args(annotation) if a is not type(None)]
        optional = len(inner) < len(get_args(annotation))
        spelled = _spell(inner[0])[0] if len(inner) == 1 else "any"
        return spelled, optional
    if origin is Literal:
        return "|".join(str(a) for a in get_args(annotation)), False
    if origin in (list, tuple, set):
        (inner,) = get_args(annotation) or (Any,)
        return [_spell(inner)[0]], False
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return _fields(annotation.model_fields), False
    return _NAMES.get(annotation, "any"), False


def _fields(model_fields: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, info in model_fields.items():
        spelled, nullable = _spell(info.annotation)
        # Optional means it may be absent: it allows None, or it is a list
        # that may be empty. A plain value with a default is always present.
        optional = nullable or (isinstance(spelled, list) and not info.is_required())
        if not optional:
            out[name] = spelled
        elif isinstance(spelled, str):
            out[name] = f"{spelled}?"
        else:
            out[f"{name}?"] = spelled
    return out


def declare(kind: type[Thought]) -> dict[str, Any]:
    """A kind in the template format, as plain data."""
    parent = kind.parent()
    if parent is None:
        return {kind.kind_name(): _fields(kind.model_fields)}

    body: dict[str, Any] = {"specializes": parent.kind_name()}
    adds = _fields(kind.adds())
    if adds:
        body["adds"] = adds
    own_parts = {
        verb: (
            role.kind.kind_name()
            if role.min == 1
            else {"kind": role.kind.kind_name(), "min": role.min}
        )
        for value in vars(kind).values()
        if isinstance(value, Composition)
        for verb, role in value.roles.items()
    }
    if own_parts:
        body["parts"] = own_parts
    own_requirements = {
        verb: target.kind_name()
        for value in vars(kind).values()
        if isinstance(value, Requirement)
        for verb, target in value.edges.items()
    }
    if own_requirements:
        body["requires"] = own_requirements
    return {kind.kind_name(): body}


class _TemplateDumper(yaml.SafeDumper):
    """Groups on their own lines, a list of plain types inline: `[text]`."""

    def represent_list(self, data: Any) -> yaml.Node:
        inline = all(isinstance(item, str) for item in data)
        return self.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=inline)


_TemplateDumper.add_representer(list, _TemplateDumper.represent_list)


def closure(*kinds: type[Thought]) -> list[type[Thought]]:
    """The kinds given plus every kind they depend on, in an order that loads.

    Each kind comes after the kinds it depends on. The thought is left out
    as a dependency: it is built in, and a template never declares it. Asked
    for by name, it is included, so `to_yaml(Thought)` prints it for reference.
    """
    ordered: list[type[Thought]] = []

    def visit(kind: type[Thought], *, asked: bool) -> None:
        if kind in ordered or (kind is Thought and not asked):
            return
        for needed in kind.depends_on():
            visit(needed, asked=False)
        ordered.append(kind)

    for kind in kinds:
        visit(kind, asked=True)
    return ordered


def to_yaml(*kinds: type[Thought], closed: bool = True) -> str:
    """One or more kinds as a YAML template.

    With `closed` (the default) the template also declares every kind the
    given ones depend on, so it stands on its own: a decision brings the
    question it resolves. Pass `closed=False` to write only the kinds named.
    """
    chosen = closure(*kinds) if closed else list(kinds)
    merged: dict[str, Any] = {}
    for kind in chosen:
        merged.update(declare(kind))
    return yaml.dump(merged, Dumper=_TemplateDumper, sort_keys=False, default_flow_style=False)


# --- reading a kind in ------------------------------------------------------


def _class_name(kind_name: str) -> str:
    return "".join(part.capitalize() for part in kind_name.split("_"))


def _parse(name: str, spec: Any) -> tuple[str, Any]:
    """One `adds` entry as a field name and a pydantic field definition."""
    optional = name.endswith("?")
    name = name.rstrip("?")
    if isinstance(spec, str) and spec.endswith("?"):
        optional, spec = True, spec[:-1]

    if isinstance(spec, list):
        if len(spec) != 1 or spec[0] not in _TYPES:
            raise ValueError(f"{name}: a list is written [type], such as [text]")
        annotation: Any = list[_TYPES[spec[0]]]
        non_empty = True
    elif isinstance(spec, str) and "|" in spec:
        annotation = Literal[tuple(choice.strip() for choice in spec.split("|"))]
        non_empty = False
    elif isinstance(spec, str) and spec in _TYPES:
        annotation = _TYPES[spec]
        non_empty = annotation is str
    else:
        raise ValueError(f"{name}: unknown type {spec!r}")

    if optional:
        return name, (annotation | None, None)
    if non_empty:
        return name, (annotation, Field(min_length=1))
    return name, (annotation, ...)


def _find(name: str, known: Mapping[str, type[Thought]], context: str, *, role: str | None = None) -> type[Thought]:
    if name not in known:
        if role is None:
            raise ValueError(f"{context}: no kind named {name!r} is defined")
        raise ValueError(
            f"{context}: {role} points at {name!r}, which is not declared in this template "
            f"or known here. A kind depends on the kinds its edges point at; declare {name!r} "
            f"first or load it before this template."
        )
    return known[name]


def _verbs(
    edges: Mapping[Any, Any], known: Mapping[str, type[Thought]], context: str
) -> dict[str, type[Thought]]:
    """A `requires` block as verb to kind. The verb must have come through as text."""
    out: dict[str, type[Thought]] = {}
    for verb, target in edges.items():
        _text_verb(verb, context)
        out[verb] = _find(target, known, context, role=verb)
    return out


def _roles(
    parts: Mapping[Any, Any], known: Mapping[str, type[Thought]], context: str
) -> dict[str, Role]:
    """A `parts` block as verb to role: `verb: kind`, or `verb: {kind: ..., min: n}`."""
    out: dict[str, Role] = {}
    for verb, spec in parts.items():
        _text_verb(verb, context)
        if isinstance(spec, Mapping):
            unknown = set(spec) - {"kind", "min"}
            if unknown or "kind" not in spec:
                raise ValueError(f"{context}: a part is written `{verb}: kind` or `{verb}: {{kind: ..., min: n}}`")
            out[verb] = Role(_find(spec["kind"], known, context, role=verb), int(spec.get("min", 1)))
        else:
            out[verb] = Role(_find(spec, known, context, role=verb))
    return out


def _text_verb(verb: Any, context: str) -> None:
    if not isinstance(verb, str):
        # YAML 1.1 reads on, off, yes, and no as booleans. Quote them or pick another word.
        raise ValueError(
            f"{context}: the verb {verb!r} is not text. "
            "YAML reads on, off, yes, and no as true or false; quote the word or choose another."
        )


def load_kinds(
    source: str | Mapping[str, Any],
    *,
    kinds: Mapping[str, type[Thought]] | None = None,
) -> dict[str, type[Thought]]:
    """Build every kind in a template, in order. Later ones may use earlier ones.

    A kind the process already knows, declared the same way, is reused
    rather than built again. The same name with a different declaration
    is an error.
    """
    template = yaml.safe_load(source) if isinstance(source, str) else source
    known = dict(kinds) if kinds is not None else all_kinds()
    built: dict[str, type[Thought]] = {}

    for name, body in template.items():
        unknown = set(body) - {"specializes", "adds", "parts", "requires"}
        if unknown:
            raise ValueError(
                f"{name}: unknown key {sorted(unknown)[0]!r}. "
                "A kind has specializes, adds, parts, and requires."
            )
        if "specializes" not in body:
            raise ValueError(
                f"{name}: a kind names the kind it specializes. "
                "Only the thought has no parent, and it is not loaded from a template."
            )
        if name in known:
            # A template that declares a kind this process already has is
            # importing it, not redeclaring it. Two classes with one name and
            # one shape would both fit the same claims, and `read` would have
            # to fall back to what they share. Reuse the one we have, or
            # refuse if the template means something else by the name.
            if declare(known[name]).get(name) == body:
                built[name] = known[name]
                continue
            raise ValueError(
                f"{name}: a kind with this name is already defined and differs from this "
                "declaration. Rename one of them; there are no namespaces yet."
            )
        # Resolve everything before building, so a template that fails
        # leaves no half-made kind behind in the registry.
        parent = _find(body["specializes"], known, name)
        fields = dict(_parse(n, spec) for n, spec in (body.get("adds") or {}).items())
        made_of = _roles(body.get("parts") or {}, known, name)
        owed = _verbs(body.get("requires") or {}, known, name)

        model = create_model(_class_name(name), __base__=parent, **fields)
        model.__kind__ = name
        if made_of:
            model.parts = Composition(**made_of)
        if owed:
            model.needs = Requirement(**owed)

        known[name] = built[name] = model
    return built


def load_kind(
    source: str | Mapping[str, Any],
    *,
    kinds: Mapping[str, type[Thought]] | None = None,
) -> type[Thought]:
    """Build the one kind a template declares."""
    built = load_kinds(source, kinds=kinds)
    if len(built) != 1:
        raise ValueError(f"expected one kind, found {len(built)}; use load_kinds")
    return next(iter(built.values()))
