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
      adds:
        chosen: text
        alternatives: [text]
        rationale: text
      requires:
        resolves: question

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
from .relations import Composition, Requirement
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
    own_composition = next(
        (v for v in vars(kind).values() if isinstance(v, Composition)), None
    )
    if own_composition is not None:
        made_of: dict[str, Any] = {"min": own_composition.min}
        if own_composition.parts:
            made_of["parts"] = [p.kind_name() for p in own_composition.parts]
        if own_composition.allows is not None:
            made_of["allows"] = [a.kind_name() for a in own_composition.allows]
        body["composed_of"] = made_of
    adds = _fields(kind.adds())
    if adds:
        body["adds"] = adds
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


def to_yaml(*kinds: type[Thought]) -> str:
    """One or more kinds as a YAML template."""
    merged: dict[str, Any] = {}
    for kind in kinds:
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


def _find(name: str, known: Mapping[str, type[Thought]], context: str) -> type[Thought]:
    if name not in known:
        raise ValueError(f"{context}: no kind named {name!r} is defined")
    return known[name]


def load_kinds(
    source: str | Mapping[str, Any],
    *,
    kinds: Mapping[str, type[Thought]] | None = None,
) -> dict[str, type[Thought]]:
    """Build every kind in a template, in order. Later ones may use earlier ones."""
    template = yaml.safe_load(source) if isinstance(source, str) else source
    known = dict(kinds) if kinds is not None else all_kinds()
    built: dict[str, type[Thought]] = {}

    for name, body in template.items():
        if "specializes" not in body:
            raise ValueError(
                f"{name}: a kind names the kind it specializes. "
                "Only the thought has no parent, and it is not loaded from a template."
            )
        parent = _find(body["specializes"], known, name)
        fields = dict(_parse(n, spec) for n, spec in (body.get("adds") or {}).items())
        model = create_model(_class_name(name), __base__=parent, **fields)
        model.__kind__ = name

        made_of = body.get("composed_of")
        if made_of:
            model.parts = Composition(
                *[_find(p, known, name) for p in made_of.get("parts", [])],
                allows=(
                    [_find(a, known, name) for a in made_of["allows"]]
                    if "allows" in made_of
                    else None
                ),
                min=made_of.get("min", 2),
            )
        owed = body.get("requires")
        if owed:
            model.needs = Requirement(
                **{verb: _find(target, known, name) for verb, target in owed.items()}
            )

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
