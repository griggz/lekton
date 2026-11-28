# Examples

Each script shows one idea, prints what it does, and checks itself with asserts. The test suite runs all of them.

```bash
uv run python examples/thought_to_decision.py
```

| Script | What it shows |
|---|---|
| [thought_to_decision.py](thought_to_decision.py) | Record a thought, promote it to a decision, resolve a question |
| [define_a_kind.py](define_a_kind.py) | Your own kinds in Python, including one made of other claims |
| [kinds_from_yaml.py](kinds_from_yaml.py) | Kinds built from [kinds.yaml](kinds.yaml) with no code |
| [kinds_for_a_mind.py](kinds_for_a_mind.py) | One person's own kinds from [mind.yaml](mind.yaml): insight, regularity, practice, event, position, answer |
| [read_a_foreign_claim.py](read_a_foreign_claim.py) | A kind you have never seen, and a label that is wrong |
| [check_model_output.py](check_model_output.py) | The loop for an agent: schema, check, feedback |
