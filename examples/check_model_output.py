"""The loop for an agent: hand a model a schema, check what comes back,
and send it what is missing.

No model is called here. `first_try` and `second_try` stand in for two
responses so the example runs offline.

Run it:  uv run python examples/check_model_output.py
"""

import json

from lekton import Decision, Record, Thought, check, read

# 1. The schema to give the model. A decision adds no fields to a thought,
#    so the claim's own schema is the thought's. Take out the fields your
#    code sets: the id, the record, the links.
schema = Thought.model_json_schema()
for yours in ("id", "record", "links"):
    schema["properties"].pop(yours, None)
schema["required"] = [name for name in schema["required"] if name in schema["properties"]]
print("for each claim the model supplies:", ", ".join(schema["required"]))
assert schema["required"] == ["body", "about"]

#    What makes it a decision is the other claims around it. Ask the model
#    for those as claims too, one list per role, using the same schema.
roles = {verb: role.kind.kind_name() for verb, role in Decision.composition().items()}
owed = {verb: kind.kind_name() for verb, kind in Decision.requirements().items()}
print("and alongside it, lists of:", roles, "| owed:", owed)

# The record is facts about the capture. Your code sets it, not the model.
record = Record(author="dana", captured_from="Monday planning call").model_dump(mode="json")


def assemble(answer: dict) -> tuple[dict, list[Thought]]:
    """The model's answer as one claim plus the claims in each role, linked."""
    parts = []
    links = []
    for verb in (*roles, *owed):
        for raw in answer.get(verb, []):
            part = Thought.model_validate({**raw, "record": record})
            parts.append(part)
            # The model drew this edge, not the speaker. Say so on the edge.
            links.append(
                {"verb": verb, "to": part.ref().model_dump(), "basis": "inferred", "by": "model"}
            )
    claim = {k: v for k, v in answer.items() if k not in roles and k not in owed}
    return {**claim, "record": record, "links": links}, parts


# 2. The model's first answer names a choice and nothing it was chosen over.
first_try = {
    "body": "We are stopping the weekly PDF report.",
    "about": [{"thing": "weekly PDF report"}],
    "passed_over": [],
    "because": [{"body": "Three opens in eight weeks.", "about": [{"thing": "weekly PDF report"}]}],
}

claim, parts = assemble(first_try)
report = check(claim, Decision, known=parts)
print(f"first try:  fits={report.fits}")
assert not report.fits

# 3. `check` did not raise. Turn the report into feedback for the model.
feedback = {name: report.detail[name] for name in report.missing}
print("send back: ", json.dumps(feedback))

#    If the model cannot fill the gap, store the claim as what it is.
fallback = read(claim, known=parts)
print(f"stored for now as a {fallback.kind}, with {len(parts)} linked claim(s)")
assert fallback.kind == "thought"

# 4. The second answer adds what was actually said on the call.
second_try = {
    **first_try,
    "passed_over": [{"body": "Send it monthly instead.", "about": [{"thing": "weekly PDF report"}]}],
}
claim, parts = assemble(second_try)
report = check(claim, Decision, known=parts)
print(f"second try: fits={report.fits} complete={report.complete} owed={report.owed}")
assert report.fits

decision = Decision.model_validate(claim)

# 5. It is a decision now, stored as three claims and two edges. It still
#    owes a question, which is a note for the person, not a reason to reject it.
print(f"stored as a {decision.kind}; tell the person it still owes: {', '.join(report.owed)}")
