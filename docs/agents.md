# Using lekton from an agent

lekton is built to sit between a model and a store of claims. The model proposes a claim, lekton says what it is and what is missing, and the result goes back to the model or to the person it works for.

## The loop

1. **Hand the model a schema.** Every kind is a Pydantic model, so `Decision.model_json_schema()` is a JSON Schema you can use as a tool's input schema or as a structured-output format.
2. **Take what comes back as data.** Do not trust the label the model put on it.
3. **Run `check`.** It never raises on a claim that falls short. It returns a `Report`.
4. **Act on the report.** Send `missing` back to the model to fix, or store the claim as the kind it actually fits.

```python
from lekton import Decision, check, read

schema = Decision.model_json_schema()      # give this to the model

report = check(model_output, Decision)     # model_output is a plain dict
if report.fits:
    claim = Decision.model_validate(model_output)
else:
    claim = read(model_output)             # stored as what it really is
    feedback = {name: report.detail[name] for name in report.missing}
```

A runnable version is in [`examples/check_model_output.py`](../examples/check_model_output.py).

## What each part of a report means for an agent

| Report says | What to do |
|---|---|
| `missing` is not empty | It is not this kind. Ask for the missing fields, or store it as a thought |
| `owed` is not empty | It is this kind, with an edge outstanding. Store it and say what is owed |
| `unverified` is not empty | An edge points at a claim you did not pass in `known`. Look it up and check again |
| `revised` is not empty | Something this claim rests on has changed since. Tell the person |

## Fields the model should not fill

The record is a set of facts about the capture, not content. Set it in your own code:

- `id`: let it generate.
- `record.author`: the person the agent is working for, or the agent itself if it is the one asserting.
- `record.recorded_at`: let it default to now.
- `record.captured_from`: the call, document, or session.

The model fills `body`, `about`, the `assertion` if there is one, and the fields the kind adds.

`model_json_schema()` includes all of these fields and marks `record` as required, so take `id`, `record`, and `links` out of the schema before you hand it to a model. The example does this in four lines.

## Being honest on someone's behalf

These are judgment calls the library leaves to you. It will not catch them.

- **Do not invent an alternative to make a decision fit.** If nothing was passed over, it is a thought.
- **Leave modality `unstated` when the speaker gave no sign.** Set `basis` to `stated` only when their own words carried it ("I think", "she told me"), and `inferred` when you read it in.
- **Keep `body` verbatim.** The assertion is where the reduction goes.
- **Promote, do not edit.** When a thought becomes a decision, call `promote`. The thought stays as it was said.
- **Look for the question first.** A decision owes one. Search the open questions you can see before writing a new one.

## Kinds a person defines

A person can describe a kind in a sentence and an agent can write it as a template:

```yaml
risk:
  specializes: thought
  adds:
    likelihood: low|medium|high
    impact: text
```

`load_kinds` turns that into a working kind at once. See [Template format](template-format.md).

## Installing the skill

`skills/lekton/SKILL.md` carries the guidance on this page in a form coding agents can load. With the [Skills CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add griggz/lekton --skill lekton
```
