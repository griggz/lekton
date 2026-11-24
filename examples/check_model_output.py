"""The loop for an agent: hand a model a schema, check what comes back,
and send it what is missing.

No model is called here. `first_try` and `second_try` stand in for two
responses so the example runs offline.

Run it:  uv run python examples/check_model_output.py
"""

import json

from lekton import Decision, Record, check, read

# 1. The schema to give the model, as a tool input or a structured output.
#    Take out the fields your own code sets: the id, the record, the links.
schema = Decision.model_json_schema()
for yours in ("id", "record", "links"):
    schema["properties"].pop(yours, None)
schema["required"] = [name for name in schema["required"] if name in schema["properties"]]
print("the model must supply:", ", ".join(schema["required"]))
assert schema["required"] == ["body", "about", "chosen", "alternatives", "rationale"]

# The record is facts about the capture. Your code sets it, not the model.
record = Record(author="dana", captured_from="Monday planning call").model_dump(mode="json")

# 2. The model's first answer names a choice and nothing it was chosen over.
first_try = {
    "body": "We are stopping the weekly PDF report.",
    "about": [{"thing": "weekly PDF report"}],
    "chosen": "Stop sending the weekly PDF report",
    "alternatives": [],
    "rationale": "Three opens in eight weeks.",
}

report = check({**first_try, "record": record}, Decision)
print(f"first try:  fits={report.fits}")
assert not report.fits

# 3. `check` did not raise. Turn the report into feedback for the model.
feedback = {name: report.detail[name] for name in report.missing}
print("send back: ", json.dumps(feedback))

#    If the model cannot fill the gap, store the claim as what it is.
fallback = read({**first_try, "record": record})
print(f"stored for now as a {fallback.kind}")
assert fallback.kind == "thought"

# 4. The second answer fills it from what was actually said on the call.
second_try = {**first_try, "alternatives": ["Send it monthly instead"]}
report = check({**second_try, "record": record}, Decision)
print(f"second try: fits={report.fits} complete={report.complete} owed={report.owed}")
assert report.fits

decision = Decision.model_validate({**second_try, "record": record})

# 5. It is a decision now. It still owes a question, which is a note for
#    the person, not a reason to reject it.
print(f"stored as a {decision.kind}; tell the person it still owes: {', '.join(report.owed)}")
