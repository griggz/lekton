"""A thought becomes a decision, and the decision answers a question.

Run it:  uv run python examples/thought_to_decision.py
"""

from lekton import Assertion, Decision, Question, Record, Thought, check, promote, status

# 1. Someone says something. That is a thought.
thought = Thought(
    record=Record(author="dana", captured_from="Monday planning call"),
    body="I do not think anyone reads the weekly PDF report anymore.",
    about=[{"thing": "weekly PDF report", "role": "subject"}, "analytics dashboard"],
    # "I do not think": a guess, and the speaker's own words say so.
    assertion=Assertion(predicate="is no longer read", modality="hypothesis", basis="stated"),
)
print(f"{thought.kind}: {thought.body}")

# 2. The question it raises. Note there is no status field.
question = Question(
    record=Record(author="dana", captured_from="Monday planning call"),
    body="Do we keep sending the weekly PDF report?",
    about=["weekly PDF report"],
    settled_by="Open counts for the last eight weeks, then a call from Dana.",
    owner="dana",
)
print(f"{question.kind}: {question.body} -> {status(question, [])}")

# 3. A week later, a choice is made. Promoting does not edit the thought.
#    It makes a new claim that points back at it.
decision = promote(
    thought,
    Decision,
    captured_from="Following Monday's call",
    body="We are stopping the weekly PDF report. The dashboard stays.",
    chosen="Stop sending the weekly PDF report",
    alternatives=["Send it monthly instead", "Keep sending it weekly"],
    rationale="Three opens in eight weeks, all from the team that builds it.",
    assertion=Assertion(predicate="is discontinued", modality="asserted", basis="stated"),
)
assert decision.id != thought.id
assert thought.assertion.modality == "hypothesis"  # the thought is as it was said

# 4. It is a decision, but it owes a question.
report = check(decision)
print(f"{decision.kind}: fits={report.fits} complete={report.complete} owed={report.owed}")
assert report.fits and not report.complete

# 5. Link it to the question it answers. Now it is complete, and the
#    question's status follows from the edge.
decision = decision.with_link("resolves", question)
report = check(decision, known=[question])
print(f"{decision.kind}: fits={report.fits} complete={report.complete}")
print(f"{question.kind}: {status(question, [decision])}")
assert report.complete
assert status(question, [decision]) == "answered"
