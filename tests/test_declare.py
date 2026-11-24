from __future__ import annotations

import pytest
from pydantic import ValidationError

from lekton import Decision, Question, Record, Thought, check, declare, load_kind, load_kinds, to_yaml

from .conftest import Bet

TEMPLATE = """
hazard:
  specializes: thought
  adds:
    likelihood: low|medium|high
    impact: text
    seen_on: date?

wager:
  specializes: thought
  composed_of:
    min: 2
    parts: [decision, hazard]
  adds:
    thesis: text
    tags?: [text]
  requires:
    resolves: question
"""


def test_the_shipped_kinds_declare_as_we_drew_them():
    assert declare(Question) == {
        "question": {
            "specializes": "thought",
            "adds": {"settled_by": "text", "owner": "text?"},
        }
    }
    assert declare(Decision) == {
        "decision": {
            "specializes": "thought",
            "adds": {"chosen": "text", "alternatives": ["text"], "rationale": "text"},
            "requires": {"resolves": "question"},
        }
    }


def test_the_thought_declares_with_no_parent_line():
    declared = declare(Thought)["thought"]
    assert "specializes" not in declared
    assert declared["record"]["author"] == "text"
    assert declared["assertion?"]["modality"] == "asserted|hypothesis|forecast|reported|unstated"
    assert declared["assertion?"]["basis"] == "stated|inferred?"


def test_a_composite_declares_its_parts():
    assert declare(Bet)["bet"]["composed_of"] == {"min": 2, "parts": ["decision", "risk"]}


def test_a_kind_can_be_built_from_a_template_with_no_code():
    built = load_kinds(TEMPLATE)
    hazard, wager = built["hazard"], built["wager"]

    assert hazard.kind_name() == "hazard"
    assert hazard.parent() is Thought
    assert wager.composition().parts == (Decision, hazard)
    assert wager.requirements() == {"resolves": Question}

    claim = hazard(
        record=Record(author="wayne"),
        body="Someone depends on arbitrary Cypher.",
        about=["traverse tool"],
        likelihood="low",
        impact="one workflow breaks",
    )
    assert claim.kind == "hazard"
    assert check(claim).complete

    with pytest.raises(ValidationError):  # not one of the choices
        hazard(**{**claim.model_dump(), "likelihood": "certain"})
    with pytest.raises(ValidationError):  # required text may not be empty
        hazard(**{**claim.model_dump(), "impact": ""})


def test_a_template_survives_the_round_trip():
    built = load_kinds(TEMPLATE)
    again = load_kinds(to_yaml(built["hazard"], built["wager"]))
    assert declare(again["hazard"]) == declare(built["hazard"])
    assert declare(again["wager"]) == declare(built["wager"])
    assert declare(built["wager"])["wager"] == {
        "specializes": "thought",
        "composed_of": {"min": 2, "parts": ["decision", "hazard"]},
        "adds": {"thesis": "text", "tags?": ["text"]},
        "requires": {"resolves": "question"},
    }


def test_a_kind_must_name_a_parent_that_exists():
    with pytest.raises(ValueError, match="no kind named 'hunch'"):
        load_kind({"guess": {"specializes": "hunch", "adds": {"odds": "number"}}})
    with pytest.raises(ValueError, match="names the kind it specializes"):
        load_kind({"guess": {"adds": {"odds": "number"}}})


def test_a_template_may_not_redefine_what_it_inherits():
    with pytest.raises(TypeError, match="redefines body"):
        load_kind({"shout": {"specializes": "thought", "adds": {"body": "integer"}}})
