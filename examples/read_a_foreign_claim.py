"""Read claims from somewhere else: a kind you have never seen, and a label that is wrong.

Run it:  uv run python examples/read_a_foreign_claim.py
"""

from lekton import Decision, Thought, check, qualifies, read

# 1. A claim arrives from another graph. Its kind, "vendor_selection", is
#    not defined here. It has everything a decision has, plus two fields.
#    Its parts live in that graph too, so the edges carry a graph name.
foreign = {
    "kind": "vendor_selection",
    "id": "a1b2c3",
    "record": {"author": "sam", "recorded_at": "2026-10-02T15:00:00Z", "version": 3},
    "body": "We are going with Northwind for payroll.",
    "about": [{"thing": "payroll"}, {"thing": "Northwind"}],
    "links": [
        {"verb": "passed_over", "to": {"id": "d4e5f6", "version": 1, "graph": "sam"}},
        {"verb": "passed_over", "to": {"id": "0718aa", "version": 1, "graph": "sam"}},
        {"verb": "because", "to": {"id": "b2c3d4", "version": 2, "graph": "sam"}},
    ],
    "vendor": "Northwind",
    "contract_ends": "2027-09-30",
}

claim = read(foreign)
print(f"labelled {foreign['kind']!r}, read as a {claim.kind}")
print(f"extra fields kept: vendor={claim.vendor}, contract_ends={claim.contract_ends}")
assert type(claim) is Decision
assert claim.model_dump()["contract_ends"] == "2027-09-30"  # nothing dropped

# The parts could not be looked up, and the report says so rather than
# pretending. Fetch them from Sam's graph and check again with `known`.
report = check(claim)
print(f"unverified until Sam's claims are fetched: {report.unverified}")
assert report.fits and not report.complete

# 2. A claim arrives labelled "decision" with nothing passed over.
mislabelled = {
    "kind": "decision",
    "record": {"author": "sam"},
    "body": "We should probably look at switching payroll vendors.",
    "about": ["payroll"],
    "urgency": "low",
}

report = check(mislabelled, Decision)
print(f"labelled 'decision': fits={report.fits}, missing={report.missing}")
print(f"what it qualifies as: {[k.kind_name() for k in qualifies(mislabelled)]}")
claim = read(mislabelled)
print(f"read as a {claim.kind}, extra field kept: urgency={claim.urgency!r}")
assert not report.fits
assert type(claim) is Thought
