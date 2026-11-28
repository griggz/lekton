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

# 3. Other things said on the call are thoughts too: the option nobody took,
#    and the reason. They are claims of their own, not fields on the decision.
alternative = Thought(
    record=Record(author="dana", captured_from="Following Monday's call"),
    body="We could send it monthly instead.",
    about=["weekly PDF report"],
)
rationale = Thought(
    record=Record(author="dana", captured_from="Following Monday's call"),
    body="Three opens in eight weeks, all from the team that builds it.",
    about=["weekly PDF report"],
    assertion=Assertion(predicate="was opened three times in eight weeks", modality="asserted", basis="stated"),
)

# 4. A week later, a choice is made. Promoting does not edit the thought.
#    It makes a new claim that points back at it. The decision's body is
#    the commitment itself; what was chosen is not a separate field.
decision = promote(
    thought,
    Decision,
    captured_from="Following Monday's call",
    body="We are stopping the weekly PDF report. The dashboard stays.",
    assertion=Assertion(predicate="is discontinued", modality="asserted", basis="stated"),
)
assert decision.id != thought.id
assert thought.assertion.modality == "hypothesis"  # the thought is as it was said

# 5. With nothing passed over, it is not a decision yet. The alternative and
#    the reason hang off it as edges; the parts stay as they were said.
print(f"{decision.kind} before linking: fits={check(decision).fits} missing={check(decision).missing}")
assert not check(decision).fits

#    Dana said the reason in so many words, so that edge is `stated`. Nobody
#    said "the alternative was monthly"; the recorder read it in: `inferred`.
decision = decision.with_link("passed_over", alternative, basis="inferred").with_link(
    "because", rationale, basis="stated"
)
report = check(decision, known=[alternative, rationale])
print(f"{decision.kind}: fits={report.fits} complete={report.complete} owed={report.owed}")
assert report.fits and not report.complete

# 6. It is a decision, but it owes a question. Link it to the one it answers.
#    Now it is complete, and the question's status follows from the edge.
decision = decision.with_link("resolves", question)
report = check(decision, known=[question, alternative, rationale])
print(f"{decision.kind}: fits={report.fits} complete={report.complete}")
print(f"{question.kind}: {status(question, [decision])}")
assert report.complete
assert status(question, [decision]) == "answered"

# 7. Because the reason is a claim, it can be contradicted on its own later,
#    without touching the decision. That is why it is not a string field.
finance = Thought(
    record=Record(author="sam", captured_from="month-end close"),
    body="Finance opened it every month for the close. Those opens were not counted.",
    about=["weekly PDF report", "finance team"],
)
print(f"{finance.kind} from {finance.record.author} can now be linked against the rationale, not the decision")
