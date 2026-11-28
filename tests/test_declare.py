from __future__ import annotations

import pytest
from pydantic import ValidationError

from pathlib import Path

from lekton import (
    Decision,
    Question,
    Record,
    Role,
    Thought,
    check,
    closure,
    declare,
    load_kind,
    load_kinds,
    to_yaml,
)

from .conftest import Bet, Risk

TEMPLATE = """
hazard:
  specializes: thought
  adds:
    likelihood: low|medium|high
    impact: text
    seen_on: date?

wager:
  specializes: thought
  adds:
    thesis: text
    tags?: [text]
  parts:
    backs: decision
    exposed_to: hazard
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
            "parts": {"passed_over": "thought"},
            "requires": {"because": "thought", "resolves": "question"},
        }
    }


def test_the_thought_declares_with_no_parent_line():
    assert "record:" in to_yaml(Thought)  # asked for by name, it prints
    assert "thought:" not in to_yaml(Decision)  # as a dependency, it does not
    declared = declare(Thought)["thought"]
    assert "specializes" not in declared
    assert declared["record"]["author"] == "text"
    assert declared["assertion?"]["modality"] == "asserted|hypothesis|forecast|reported|unstated"
    assert declared["assertion?"]["basis"] == "stated|inferred?"


def test_a_composite_declares_its_parts_by_role():
    assert declare(Bet)["bet"]["parts"] == {"backs": "decision", "exposed_to": "risk"}


def test_a_kind_can_be_built_from_a_template_with_no_code():
    built = load_kinds(TEMPLATE)
    hazard, wager = built["hazard"], built["wager"]

    assert hazard.kind_name() == "hazard"
    assert hazard.parent() is Thought
    assert wager.composition() == {"backs": Role(Decision), "exposed_to": Role(hazard)}
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
        "adds": {"thesis": "text", "tags?": ["text"]},
        "parts": {"backs": "decision", "exposed_to": "hazard"},
        "requires": {"resolves": "question"},
    }


# --- dependencies between kinds ----------------------------------------------


def test_a_kind_knows_the_kinds_it_depends_on():
    assert Decision.depends_on() == [Thought, Question]
    assert Question.depends_on() == [Thought]
    assert Bet.depends_on() == [Thought, Decision, Risk]


def test_a_template_writes_out_closed_so_a_decision_brings_its_question():
    import yaml

    assert [k.kind_name() for k in closure(Decision)] == ["question", "decision"]
    assert [k.kind_name() for k in closure(Bet)] == ["question", "decision", "risk", "bet"]
    assert list(yaml.safe_load(to_yaml(Bet))) == ["question", "decision", "risk", "bet"]
    assert "question:" not in to_yaml(Decision, closed=False)


def test_a_closed_template_loads_with_nothing_but_the_thought_known():
    riddle_and_call = """
riddle:
  specializes: thought
  adds:
    settled_by: text
call:
  specializes: thought
  parts:
    passed_over: thought
  requires:
    resolves: riddle
"""
    built = load_kinds(riddle_and_call, kinds={"thought": Thought})
    closed = to_yaml(built["call"])
    again = load_kinds(closed, kinds={"thought": Thought})
    assert list(again) == ["riddle", "call"]
    assert declare(again["call"]) == declare(built["call"])


def test_a_template_that_declares_a_kind_we_already_have_imports_it():
    # The shipped template, loaded here, hands back the shipped classes.
    import lekton

    built = load_kinds((Path(lekton.__file__).parent / "kinds.yaml").read_text())
    assert built["question"] is Question
    assert built["decision"] is Decision
    # A closed export of our own composite comes back as our own classes too.
    assert load_kinds(to_yaml(Bet))["bet"] is Bet


def test_the_same_name_with_a_different_shape_is_refused():
    with pytest.raises(ValueError, match="already defined and differs"):
        load_kind({"question": {"specializes": "thought", "adds": {"settled_by": "text", "asked_on": "date"}}})


def test_a_decision_without_a_question_in_reach_is_an_error_that_says_so():
    with pytest.raises(ValueError, match="resolves points at 'question'"):
        load_kinds(to_yaml(Decision, closed=False), kinds={"thought": Thought})


def test_the_shipped_template_file_says_what_the_shipped_classes_say():
    import yaml

    import lekton

    shipped = yaml.safe_load((Path(lekton.__file__).parent / "kinds.yaml").read_text())
    assert shipped == {**declare(Question), **declare(Decision)}
    assert list(shipped) == ["question", "decision"]  # dependency order


def test_a_kind_must_name_a_parent_that_exists():
    with pytest.raises(ValueError, match="no kind named 'hunch'"):
        load_kind({"guess": {"specializes": "hunch", "adds": {"odds": "number"}}})
    with pytest.raises(ValueError, match="names the kind it specializes"):
        load_kind({"guess": {"adds": {"odds": "number"}}})


def test_a_key_the_format_does_not_know_is_refused():
    # Silently ignoring one would load a kind with less than the author meant.
    with pytest.raises(ValueError, match="unknown key 'composed_of'"):
        load_kind({"wager": {"specializes": "thought", "composed_of": {"parts": ["decision"]}}})


def test_a_template_that_fails_leaves_no_kind_behind():
    from lekton import kinds

    with pytest.raises(ValueError):
        load_kind({"stub": {"specializes": "thought", "parts": {"backs": "nothing_here"}}})
    assert "stub" not in kinds()


def test_a_part_with_a_minimum_round_trips_through_the_template():
    rule = load_kind("rule:\n  specializes: thought\n  parts:\n    seen_in: {kind: thought, min: 2}\n")
    assert rule.composition() == {"seen_in": Role(Thought, min=2)}
    assert declare(rule)["rule"]["parts"] == {"seen_in": {"kind": "thought", "min": 2}}
    # A minimum of one is written the short way.
    assert declare(Decision)["decision"]["parts"] == {"passed_over": "thought"}
    assert load_kind(to_yaml(rule, closed=False)) is rule


def test_a_part_spelled_wrong_is_refused():
    with pytest.raises(ValueError, match="a part is written"):
        load_kind({"misrule": {"specializes": "thought", "parts": {"seen_in": {"type": "thought"}}}})
    with pytest.raises(ValueError, match="a part is written"):
        load_kind({"misrule": {"specializes": "thought", "parts": {"seen_in": {"kind": "thought", "max": 3}}}})


def test_a_part_must_name_a_kind_that_exists():
    # A fresh name: kinds register per process, and one declared by an
    # earlier test may still be alive, which would trip the same-name check first.
    with pytest.raises(ValueError, match="backs points at 'hunch'"):
        load_kind({"punt": {"specializes": "thought", "parts": {"backs": "hunch"}}})


def test_a_verb_yaml_read_as_a_boolean_is_refused_with_a_reason():
    with pytest.raises(ValueError, match="quote the word"):
        load_kind("gamble:\n  specializes: thought\n  parts:\n    on: decision\n")
    # Quoted, it is text like any other verb, and it writes back out quoted.
    gamble = load_kind("gamble:\n  specializes: thought\n  parts:\n    'on': decision\n")
    assert gamble.composition() == {"on": Role(Decision)}
    assert load_kind(to_yaml(gamble, closed=False)).composition() == {"on": Role(Decision)}


def test_a_template_may_not_redefine_what_it_inherits():
    with pytest.raises(TypeError, match="redefines body"):
        load_kind({"shout": {"specializes": "thought", "adds": {"body": "integer"}}})
