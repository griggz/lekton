"""Define your own kinds in Python: one that adds fields, one made of other claims.

Run it:  uv run python examples/define_a_kind.py
"""

from lekton import Decision, Record, Thought, check, composed_of, to_yaml


# is-a: a risk is a thought with two more fields. Both are about the claim
# itself (how likely, how bad), which is what makes them fields and not
# claims of their own.
class Risk(Thought):
    likelihood: str
    impact: str


# made-of: a bet is a thought that backs a decision and is exposed to a
# risk. Each role is a verb; the edge on the claim carries it.
class Bet(Thought):
    thesis: str
    parts = composed_of(backs=Decision, exposed_to=Risk)


print(to_yaml(Risk, Bet))

alternative = Thought(
    record=Record(author="dana"),
    body="We could send it monthly instead.",
    about=["weekly PDF report"],
)
decision = Decision(
    record=Record(author="dana"),
    body="We are stopping the weekly PDF report.",
    about=["weekly PDF report"],
).with_link("passed_over", alternative)
risk = Risk(
    record=Record(author="dana"),
    body="Finance may rely on the PDF for their month-end close.",
    about=["weekly PDF report", "finance team"],
    likelihood="low",
    impact="one team loses a number they need",
)

bet = Bet(
    record=Record(author="dana"),
    body="Nobody will miss the PDF.",
    about=["weekly PDF report"],
    thesis="The dashboard already covers every use of the report",
)

# With no parts, it is not yet a bet.
report = check(bet)
print(f"no parts:   fits={report.fits} missing={report.missing}")
assert not report.fits

# Each edge pins the version of the part it points at.
bet = bet.with_link("backs", decision).with_link("exposed_to", risk)
everything = [decision, risk, alternative]
report = check(bet, known=everything)
print(f"with parts: fits={report.fits}")
assert report.fits

# A part in the wrong role does not count: a risk is not a decision.
wrong = Bet(
    record=Record(author="dana"),
    body="Nobody will miss the PDF.",
    about=["weekly PDF report"],
    thesis="The dashboard already covers every use of the report",
).with_link("backs", risk).with_link("exposed_to", risk)
report = check(wrong, known=everything)
print(f"wrong role: fits={report.fits} missing={report.missing}")
assert not report.fits

# If a part is revised later, the bet is unchanged and the check says so.
revised = risk.model_copy(update={"record": risk.record.model_copy(update={"version": 2})})
report = check(bet, known=[decision, revised, alternative])
print(f"part revised: {report.revised}")
assert report.fits and report.revised
