from __future__ import annotations

import pytest
from pydantic import ValidationError

from lekton import Assertion, Decision, Question, Record, Thought, kinds

from .conftest import Bet, Position, Risk


def test_a_thought_needs_an_author_a_body_and_one_thing_it_is_about():
    with pytest.raises(ValidationError):
        Thought(record=Record(author="wayne"), body="Nothing to hang this on.", about=[])


def test_plain_strings_are_read_as_things(thought):
    assert [a.thing for a in thought.about] == ["traverse tool", "Postgres port", "Cypher"]
    assert thought.about[0].role == "subject"
    assert thought.about[1].role is None


def test_a_role_without_an_assertion_is_refused():
    with pytest.raises(ValidationError, match="only means something"):
        Thought(
            record=Record(author="wayne"),
            body="The traverse tool exists.",
            about=[{"thing": "traverse tool", "role": "subject"}],
        )


def test_modality_is_unstated_until_someone_says_otherwise():
    # The default must never claim firm footing for a claim nobody examined.
    assertion = Assertion(predicate="is never used by me")
    assert assertion.modality == "unstated"
    assert assertion.basis is None


def test_basis_says_how_the_modality_is_known(thought):
    assert thought.assertion.modality == "hypothesis"
    assert thought.assertion.basis == "stated"
    guessed = Assertion(predicate="is never used", modality="hypothesis", basis="inferred")
    assert guessed.basis == "inferred"


def test_an_unstated_modality_cannot_carry_a_basis():
    with pytest.raises(ValidationError, match="has no basis"):
        Assertion(predicate="is never used", basis="inferred")


def test_a_questions_assertion_is_unstated(question):
    # A question asserts nothing until its blank is filled.
    asked = question.model_copy(
        update={"assertion": Assertion(predicate="comes along in the port")}
    )
    assert asked.assertion.modality == "unstated"
    assert asked.assertion.value is None


def test_kind_names_come_from_the_class():
    assert Thought.kind_name() == "thought"
    assert Decision.kind_name() == "decision"
    assert Thought.parent() is None
    assert Decision.parent() is Thought
    assert set(Decision.adds()) == {"chosen", "alternatives", "rationale"}


def test_every_defined_kind_is_findable_by_name():
    found = kinds()
    assert found["thought"] is Thought
    assert found["question"] is Question
    assert found["bet"] is Bet


def test_a_kind_may_not_redefine_what_it_inherits():
    with pytest.raises(TypeError, match="redefines body"):

        class Shout(Thought):
            body: int


def test_a_kind_with_no_required_addition_is_not_distinct():
    assert Risk.is_distinct()
    assert Bet.is_distinct()
    assert not Position.is_distinct()


def test_linking_returns_a_copy(decision, question):
    linked = decision.with_link("resolves", question)
    assert decision.links == []
    assert linked.linked("resolves") == [question.ref()]
