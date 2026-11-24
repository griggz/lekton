"""Build kinds from a YAML template, with no code written for them.

Run it:  uv run python examples/kinds_from_yaml.py
"""

from pathlib import Path

from pydantic import ValidationError

from lekton import Question, Record, check, declare, load_kinds, to_yaml

template = (Path(__file__).parent / "kinds.yaml").read_text()
built = load_kinds(template)
Risk, Experiment, Bet = built["risk"], built["experiment"], built["bet"]

print("loaded:", ", ".join(built))
print(f"experiment specializes {Experiment.parent().kind_name()}")
print(f"experiment owes: {Experiment.requirements()}")
print(f"bet is made of: {Bet.composition()}")

# The kinds work like any other.
risk = Risk(
    record=Record(author="dana"),
    body="Finance may rely on the PDF for their month-end close.",
    about=["weekly PDF report", "finance team"],
    likelihood="low",
    impact="one team loses a number they need",
)
print(f"{risk.kind}: likelihood={risk.likelihood}")
assert check(risk).complete

# The template's types are enforced.
try:
    Risk(**{**risk.model_dump(), "likelihood": "certain"})
except ValidationError as error:
    print(f"refused: {error.errors()[0]['msg']}")
else:
    raise AssertionError("an unlisted choice should be refused")

# An experiment owes a question, the same way a decision does.
experiment = Experiment(
    record=Record(author="dana"),
    body="Pause the PDF for two weeks and count who asks for it.",
    about=["weekly PDF report"],
    hypothesis="Nobody will ask",
    measure="Requests for the report in the two weeks",
    ends_on="2026-12-08",
)
question = Question(
    record=Record(author="dana"),
    body="Do we keep sending the weekly PDF report?",
    about=["weekly PDF report"],
    settled_by="Requests during the pause.",
)
print(f"experiment owes: {check(experiment).owed}")
linked = experiment.with_link("resolves", question)
assert check(linked, known=[question]).complete

# A kind writes back out as the template it came from.
print()
print(to_yaml(Risk))
assert declare(load_kinds(to_yaml(Risk))["risk"]) == declare(Risk)
