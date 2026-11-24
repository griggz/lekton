"""Define your own kinds in Python: one that adds fields, one made of other claims.

Run it:  uv run python examples/define_a_kind.py
"""

from lekton import Decision, Record, Thought, check, composed_of, to_yaml


# is-a: a risk is a thought with two more fields.
class Risk(Thought):
    likelihood: str
    impact: str


# made-of: a bet is a thought composed of a decision and a risk.
class Bet(Thought):
    thesis: str
    parts = composed_of(Decision, Risk)


print(to_yaml(Risk, Bet))

decision = Decision(
    record=Record(author="dana"),
    body="We are stopping the weekly PDF report.",
    about=["weekly PDF report"],
    chosen="Stop sending the weekly PDF report",
    alternatives=["Send it monthly instead"],
    rationale="Three opens in eight weeks.",
)
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

# Each composed_of edge pins the version of the part it points at.
bet = bet.with_link("composed_of", decision).with_link("composed_of", risk)
report = check(bet, known=[decision, risk])
print(f"with parts: fits={report.fits}")
assert report.fits

# If a part is revised later, the bet is unchanged and the check says so.
revised = risk.model_copy(update={"record": risk.record.model_copy(update={"version": 2})})
report = check(bet, known=[decision, revised])
print(f"part revised: {report.revised}")
assert report.fits and report.revised
