from __future__ import annotations

import pytest
from pydantic import ValidationError

from lekton import Decision, Question, Record, Thought, check, composed_of, qualifies, read, status

from .conftest import Bet, Risk


# --- label against structure ------------------------------------------------


def test_a_label_does_not_make_a_decision(thought):
    labelled = {**thought.model_dump(), "kind": "decision", "chosen": "Retire it"}
    report = check(labelled, Decision)
    assert not report.fits
    assert set(report.missing) == {"alternatives", "rationale"}
    assert type(read(labelled)) is Thought


def test_structure_makes_a_decision_whatever_the_label(decision):
    # The same content held as a plain thought still qualifies as a decision.
    plain = Thought.model_validate(decision.model_dump())
    assert type(plain) is Thought
    assert check(plain, Decision).fits
    assert qualifies(plain) == [Decision]
    assert type(read(plain)) is Decision


def test_an_empty_required_field_counts_as_missing(decision):
    data = {**decision.model_dump(), "alternatives": []}
    assert "alternatives" in check(data, Decision).missing


def test_data_that_is_not_a_thought_qualifies_as_nothing():
    assert qualifies({"body": "no record, nothing it is about"}) == []
    with pytest.raises(ValidationError):
        read({"body": "no record, nothing it is about"})


def test_indistinct_kinds_are_never_guessed(thought):
    # Position adds nothing required, so every thought would "be" one.
    assert qualifies(thought) == [Thought]


# --- required edges ---------------------------------------------------------


def test_a_decision_without_a_question_is_a_decision_that_owes_one(decision):
    report = check(decision)
    assert report.fits
    assert not report.complete
    assert report.owed == ("resolves: question",)


def test_a_decision_linked_to_its_question_is_complete(decision, question):
    report = check(decision.with_link("resolves", question), known=[question])
    assert report.complete


def test_an_edge_to_a_claim_we_cannot_see_is_unverified(decision, question):
    report = check(decision.with_link("resolves", question))
    assert report.fits
    assert report.owed == ()
    assert report.unverified == ("resolves: question",)
    assert not report.complete


def test_resolving_something_that_is_not_a_question_does_not_count(decision, thought):
    report = check(decision.with_link("resolves", thought), known=[thought])
    assert report.owed == ("resolves: question",)


# --- composition ------------------------------------------------------------


def bet(*parts) -> Bet:
    made = Bet(
        record=Record(author="wayne"),
        body="We can drop arbitrary Cypher and nobody will miss it.",
        about=["traverse tool"],
        thesis="No one uses it",
    )
    for part in parts:
        made = made.with_link("composed_of", part)
    return made


def test_a_composite_with_its_parts_fits(decision, risk):
    assert check(bet(decision, risk), known=[decision, risk]).fits


def test_a_composite_missing_a_part_does_not_fit(decision):
    other = decision.model_copy(update={"id": "another-decision"})
    report = check(bet(decision, other), known=[decision, other])
    assert not report.fits
    assert "composed_of: risk" in report.missing


def test_a_composite_needs_two_parts(decision):
    report = check(bet(decision), known=[decision])
    assert "composed_of" in report.missing


def test_a_part_revised_after_the_fact_shows_up_without_changing_the_bet(decision, risk):
    made = bet(decision, risk)
    newer = risk.model_copy(update={"record": risk.record.model_copy(update={"version": 2})})
    report = check(made, known=[decision, newer])
    assert report.fits
    assert report.revised == (f"composed_of: {risk.id} pinned at v1, now v2",)


def test_allows_limits_what_a_part_may_be(decision, question, risk):
    class Brief(Thought):
        parts = composed_of(allows=[Decision, Risk])

    def brief(*parts) -> Brief:
        made = Brief(record=Record(author="wayne"), body="A brief.", about=["traverse tool"])
        for part in parts:
            made = made.with_link("composed_of", part)
        return made

    everything = [decision, question, risk]
    assert check(brief(decision, risk), known=everything).fits
    assert not check(brief(decision, question), known=everything).fits


# --- reading a kind this process has never seen -----------------------------


def test_a_foreign_kind_comes_back_as_its_nearest_known_ancestor(decision):
    foreign = {
        **decision.model_dump(),
        "kind": "vendor_selection",
        "vendor": "Postgres",
        "contract_ends": "2027-06-30",
    }
    claim = read(foreign)
    assert type(claim) is Decision
    assert claim.vendor == "Postgres"  # nothing dropped
    assert claim.model_dump()["contract_ends"] == "2027-06-30"


# --- a question's status is worked out, never stored ------------------------


def test_a_question_is_open_until_something_resolves_it(question, decision):
    assert "status" not in Question.model_fields
    assert status(question, [decision]) == "open"
    answer = decision.with_link("resolves", question)
    assert status(question, [answer]) == "answered"


def test_a_question_reopens_when_its_answer_is_superseded(question, decision):
    answer = decision.with_link("resolves", question)
    reversal = Thought(
        record=Record(author="wayne"),
        body="Someone does use it after all. Retiring it is off.",
        about=["traverse tool"],
    ).with_link("supersedes", answer)
    assert status(question, [answer, reversal]) == "open"
