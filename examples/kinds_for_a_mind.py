"""Kinds for one person's own thinking, loaded from a template that declares
only what it adds. Thought, question, and decision are imported.

Run it:  uv run python examples/kinds_for_a_mind.py
"""

from pathlib import Path

from lekton import Question, Record, Thought, check, closure, load_kinds, status, to_yaml

built = load_kinds((Path(__file__).parent / "mind.yaml").read_text())
Insight, Regularity, Practice, Event, Position, Answer = (
    built["insight"],
    built["regularity"],
    built["practice"],
    built["event"],
    built["position"],
    built["answer"],
)
print("loaded:", ", ".join(built))

# Every kind depends on the thought; an answer also depends on the question.
print("answer depends on:", [k.kind_name() for k in Answer.depends_on()])
assert [k.kind_name() for k in closure(Answer)] == ["question", "answer"]

record = Record(author="dana", captured_from="weekly review")

# 1. A thought, and the insight drawn from it. The implication is a claim of
#    its own, so it can be argued with later without touching the insight.
noticed = Thought(record=record, body="Every demo that went well, I had sent the agenda the day before.",
                  about=["demos"])
follows = Thought(record=record, body="Preparation the customer can see is what makes a demo land.",
                  about=["demos"])
insight = Insight(record=record, body="The agenda is the demo.", about=["demos"])
print(f"insight alone: fits={check(insight).fits}")
assert not check(insight).fits
insight = insight.with_link("implies", follows).with_link("evolved_from", noticed)
assert check(insight, known=[follows, noticed]).complete

# 2. "Pattern" meant two things, told apart by what each calls for.
#    A regularity is asserted, and recurs: its template asks for at least two
#    sightings. One is a thought that might become one; the report says what is short.
regularity = Regularity(record=record, body="Demos land when the agenda went out the day before.",
                        about=["demos"])
regularity = regularity.with_link("seen_in", noticed)
report = check(regularity, known=[noticed])
print(f"regularity, one sighting: fits={report.fits} {report.detail}")
assert not report.fits
again = Thought(record=record, body="Northwind went the same way: agenda on Tuesday, demo on Wednesday.",
                about=["demos", "Northwind"])
regularity = regularity.with_link("seen_in", again)
print(f"regularity, two sightings: fits={check(regularity, known=[noticed, again]).fits}")
assert check(regularity, known=[noticed, again]).fits

#    A practice is an instruction. It has no truth value, so it rests on a
#    regularity instead of on sightings, and owes one until it has it.
practice = Practice(record=record, body="Send the agenda the day before.", about=["demos"],
                    applies_when="Any customer-facing session with more than two people on their side")
report = check(practice)
print(f"practice: fits={report.fits} owed={report.owed}")
assert report.fits and report.owed == ("grounded_in: regularity",)
assert check(practice.with_link("grounded_in", regularity), known=[regularity, noticed, again]).complete

# 3. An event owes an outcome, and is still an event without one.
event = Event(record=record, body="Ran the Northwind demo.", about=["Northwind", "demos"],
              occurred_at="2026-11-20T15:00:00Z")
report = check(event)
print(f"event: fits={report.fits} owed={report.owed}")
assert report.fits and report.owed == ("resulted_in: thought",)

# 4. A position carries what would prove it wrong. That is a field, not a
#    claim: it is the author's own condition, like a question's settled_by.
position = Position(record=record, body="Live demos beat recorded ones.", about=["demos"],
                    falsifier="A quarter where recorded demos convert as well.")
assert check(position).complete

# 5. An answer is made by the question it answers. A decision only owes its
#    question; an answer is not an answer without one.
question = Question(record=record, body="Do we encrypt backups at rest?", about=["backups"],
                    settled_by="A yes or no that security will sign.")
answer = Answer(record=record, body="Yes. Backups are encrypted at rest with keys we hold.",
                about=["backups"], status="approved")
print(f"answer alone: fits={check(answer).fits} missing={check(answer).missing}")
assert not check(answer).fits
answer = answer.with_link("resolves", question)
assert check(answer, known=[question]).complete
print(f"question: {status(question, [answer])}")
assert status(question, [answer]) == "answered"

# 6. Graph-wide fields ride along on any kind without being declared.
held = Position.model_validate({**position.model_dump(), "conviction": 0.8, "confidence": 0.4})
assert held.model_dump()["conviction"] == 0.8

# The template writes back out closed: the answer brings the question with it.
print()
print(to_yaml(Answer))
