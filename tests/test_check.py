from __future__ import annotations

import pytest
from pydantic import ValidationError

from lekton import Decision, Question, Record, Role, Thought, check, composed_of, qualifies, read, status

from .conftest import Bet


# --- label against structure ------------------------------------------------


def test_a_label_does_not_make_a_decision(thought):
    labelled = {**thought.model_dump(), "kind": "decision"}
    report = check(labelled, Decision)
    assert not report.fits
    assert report.missing == ("passed_over: thought",)
    assert type(read(labelled)) is Thought


def test_structure_makes_a_decision_whatever_the_label(decision, alternative, rationale):
    # The same content held as a plain thought still qualifies as a decision.
    plain = Thought.model_validate(decision.model_dump())
    parts = [alternative, rationale]
    assert type(plain) is Thought
    assert check(plain, Decision, known=parts).fits
    assert qualifies(plain, known=parts) == [Decision]
    assert type(read(plain, known=parts)) is Decision


def test_a_decision_adds_no_fields_only_roles():
    assert Decision.adds() == {}
    assert Decision.composition() == {"passed_over": Role(Thought)}
    assert Decision.requirements() == {"because": Thought, "resolves": Question}
    assert Decision.is_distinct()


def test_an_empty_required_field_counts_as_missing(question):
    data = {**question.model_dump(), "settled_by": ""}
    assert "settled_by" in check(data, Question).missing


def test_data_that_is_not_a_thought_qualifies_as_nothing():
    assert qualifies({"body": "no record, nothing it is about"}) == []
    with pytest.raises(ValidationError):
        read({"body": "no record, nothing it is about"})


def test_indistinct_kinds_are_never_guessed(thought):
    # Position adds nothing required, so every thought would "be" one.
    assert qualifies(thought) == [Thought]


# --- parts ------------------------------------------------------------------


def test_a_part_we_cannot_see_is_unverified_not_missing(decision):
    # The edge is there. Whether its target is a thought cannot be told.
    report = check(decision)
    assert report.fits
    assert "passed_over: thought" in report.unverified
    assert not report.complete


def test_a_part_that_does_not_fit_its_role_does_not_fill_it(decision, risk):
    def bet(*parts) -> Bet:
        made = Bet(
            record=Record(author="wayne"),
            body="We can drop arbitrary Cypher and nobody will miss it.",
            about=["traverse tool"],
            thesis="No one uses it",
        )
        for verb, part in parts:
            made = made.with_link(verb, part)
        return made

    everything = [decision, risk, *decision_parts(decision)]
    assert check(bet(("backs", decision), ("exposed_to", risk)), known=everything).fits

    # A risk in the `on` role is not a decision, so the role is unfilled.
    report = check(bet(("backs", risk), ("exposed_to", risk)), known=everything)
    assert not report.fits
    assert report.missing == ("backs: decision",)

    # One role filled and the other absent.
    report = check(bet(("backs", decision)), known=everything)
    assert report.missing == ("exposed_to: risk",)


def decision_parts(decision) -> list[Thought]:
    """Stand-ins for a decision's parts, so a check can see past the edge."""
    return [
        Thought(record=Record(author="wayne"), body="a part", about=["traverse tool"]).model_copy(
            update={"id": ref.id}
        )
        for ref in [*decision.linked("passed_over"), *decision.linked("because")]
    ]


def test_a_part_revised_after_the_fact_shows_up_without_changing_the_claim(
    decision, alternative, rationale
):
    newer = alternative.model_copy(
        update={"record": alternative.record.model_copy(update={"version": 2})}
    )
    report = check(decision, known=[newer, rationale])
    assert report.fits
    assert report.revised == (f"passed_over: {alternative.id} pinned at v1, now v2",)


def test_roles_are_inherited_and_added_to(decision):
    class Reversal(Decision):
        parts = composed_of(undoes=Decision)

    assert Reversal.composition() == {"passed_over": Role(Thought), "undoes": Role(Decision)}
    assert Reversal.requirements() == Decision.requirements()


# --- a role that takes more than one claim -----------------------------------


class Pattern(Thought):
    """Recurring means seen in at least two claims."""

    parts = composed_of(seen_in=(Thought, 2))


def sightings(n: int) -> list[Thought]:
    return [
        Thought(record=Record(author="wayne"), body=f"sighting {i}", about=["traverse tool"])
        for i in range(n)
    ]


def pattern(*seen: Thought) -> Pattern:
    made = Pattern(record=Record(author="wayne"), body="It keeps happening.", about=["traverse tool"])
    for claim in seen:
        made = made.with_link("seen_in", claim)
    return made


def test_a_role_with_a_minimum_counts_its_parts():
    assert Pattern.composition() == {"seen_in": Role(Thought, min=2)}
    one, two = sightings(2)
    report = check(pattern(one), known=[one])
    assert not report.fits
    assert report.missing == ("seen_in: thought",)
    assert report.detail["seen_in: thought"] == "needs 2, has 1"
    assert check(pattern(one, two), known=[one, two]).fits


def test_parts_that_cannot_be_seen_may_make_up_the_count():
    one, two = sightings(2)
    # One sighting verified, one edge to a claim not in `known`: cannot be told.
    report = check(pattern(one, two), known=[one])
    assert report.fits
    assert report.unverified == ("seen_in: thought",)


def test_a_part_of_the_wrong_kind_does_not_count_towards_the_minimum(question):
    one = sightings(1)[0]

    class Casebook(Thought):
        parts = composed_of(cases=(Question, 2))

    book = (
        Casebook(record=Record(author="wayne"), body="Cases.", about=["traverse tool"])
        .with_link("cases", question)
        .with_link("cases", one)
    )
    report = check(book, known=[question, one])
    assert report.detail["cases: question"] == "needs 2, has 1"


def test_a_role_takes_at_least_one_claim():
    with pytest.raises(ValueError, match="at least one"):
        Role(Thought, min=0)


# --- required edges ---------------------------------------------------------


def test_a_decision_without_a_question_is_a_decision_that_owes_one(
    decision, alternative, rationale
):
    report = check(decision, known=[alternative, rationale])
    assert report.fits
    assert not report.complete
    assert report.owed == ("resolves: question",)


def test_a_decision_without_a_reason_owes_one(alternative):
    bare = Decision(
        record=Record(author="wayne"),
        body="Retire the traverse tool.",
        about=["traverse tool"],
    ).with_link("passed_over", alternative)
    report = check(bare, known=[alternative])
    assert report.fits
    assert report.owed == ("because: thought", "resolves: question")


def test_a_decision_linked_to_its_question_is_complete(decision, question, alternative, rationale):
    report = check(
        decision.with_link("resolves", question), known=[question, alternative, rationale]
    )
    assert report.complete


def test_an_edge_to_a_claim_we_cannot_see_is_unverified(decision, question, alternative, rationale):
    report = check(decision.with_link("resolves", question), known=[alternative, rationale])
    assert report.fits
    assert report.owed == ()
    assert report.unverified == ("resolves: question",)
    assert not report.complete


def test_resolving_something_that_is_not_a_question_does_not_count(
    decision, thought, alternative, rationale
):
    report = check(decision.with_link("resolves", thought), known=[thought, alternative, rationale])
    assert report.owed == ("resolves: question",)


# --- reading a kind this process has never seen -----------------------------


def test_a_foreign_kind_comes_back_as_its_nearest_known_ancestor(decision, alternative, rationale):
    foreign = {
        **decision.model_dump(),
        "kind": "vendor_selection",
        "vendor": "Postgres",
        "contract_ends": "2027-06-30",
    }
    claim = read(foreign, known=[alternative, rationale])
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
