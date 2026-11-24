from __future__ import annotations

import pytest
from pydantic import ValidationError

from lekton import Assertion, Decision, check, promote


def test_promotion_makes_a_new_claim_that_points_back(thought):
    decision = promote(
        thought,
        Decision,
        body="Retire the traverse tool in the Postgres port.",
        chosen="Retire it, with no replacement",
        alternatives=["A read-only SQL tool with the same gating"],
        rationale="Unused, and already off on shared instances.",
        assertion=Assertion(predicate="is retired", modality="asserted"),
    )
    assert type(decision) is Decision
    assert decision.id != thought.id
    assert decision.record.recorded_at >= thought.record.recorded_at
    assert decision.record.captured_from is None  # its own record, not the thought's
    assert decision.linked("evolved_from") == [thought.ref()]
    assert [a.thing for a in decision.about] == [a.thing for a in thought.about]
    assert decision.assertion.modality == "asserted"

    # The thought is untouched.
    assert thought.assertion.modality == "hypothesis"
    assert thought.links == []


def test_a_promoted_decision_still_owes_its_question(thought):
    decision = promote(
        thought,
        Decision,
        chosen="Retire it",
        alternatives=["Port it"],
        rationale="Unused.",
    )
    assert check(decision).owed == ("resolves: question",)


def test_promotion_fails_without_what_the_kind_adds(thought):
    with pytest.raises(ValidationError):
        promote(thought, Decision, chosen="Retire it")


def test_promotion_only_goes_down_the_family_tree(question):
    with pytest.raises(TypeError, match="does not specialize question"):
        promote(question, Decision, chosen="x", alternatives=["y"], rationale="z")
