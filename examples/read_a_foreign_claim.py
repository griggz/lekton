"""Read claims from somewhere else: a kind you have never seen, and a label that is wrong.

Run it:  uv run python examples/read_a_foreign_claim.py
"""

from lekton import Decision, Thought, check, qualifies, read

# 1. A claim arrives from another graph. Its kind, "vendor_selection", is
#    not defined here. It has everything a decision has, plus two fields.
foreign = {
    "kind": "vendor_selection",
    "id": "a1b2c3",
    "record": {"author": "sam", "recorded_at": "2026-10-02T15:00:00Z", "version": 3},
    "body": "We are going with Northwind for payroll.",
    "about": [{"thing": "payroll"}, {"thing": "Northwind"}],
    "chosen": "Northwind",
    "alternatives": ["Contoso", "Build it in house"],
    "rationale": "Half the price, and it has the export we need.",
    "vendor": "Northwind",
    "contract_ends": "2027-09-30",
}

claim = read(foreign)
print(f"labelled {foreign['kind']!r}, read as a {claim.kind}")
print(f"extra fields kept: vendor={claim.vendor}, contract_ends={claim.contract_ends}")
assert type(claim) is Decision
assert claim.model_dump()["contract_ends"] == "2027-09-30"  # nothing dropped

# 2. A claim arrives labelled "decision" with nothing chosen over anything.
mislabelled = {
    "kind": "decision",
    "record": {"author": "sam"},
    "body": "We should probably look at switching payroll vendors.",
    "about": ["payroll"],
    "rationale": "The current one is expensive.",
}

report = check(mislabelled, Decision)
print(f"labelled 'decision': fits={report.fits}, missing={report.missing}")
print(f"what it qualifies as: {[k.kind_name() for k in qualifies(mislabelled)]}")
claim = read(mislabelled)
print(f"read as a {claim.kind}, rationale kept: {claim.rationale!r}")
assert not report.fits
assert type(claim) is Thought
