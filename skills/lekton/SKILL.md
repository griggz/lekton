---
name: lekton
description: Record, check, or define kinds of claims (thoughts, questions, decisions, and a person's own kinds) with the Python lekton library, on behalf of the person whose thinking it is.
---

# Working with claims in lekton

A claim is something a person decided, noticed, argued, or believed. lekton gives every claim one base shape, the thought, and builds every other kind by adding to it. You are usually doing this for someone else, so the job is to record what they said, not what would make a tidier record.

## Find the current API

Check the installed version of `lekton`. Read [the documentation index](https://raw.githubusercontent.com/griggz/lekton/main/llms.txt) and the pages it links for what you need. The API reference lists every public name with its arguments and result.

## Pick the kind by what the claim carries

Decide by structure, not by how the claim sounds.

| If you can fill in | It is a |
|---|---|
| Who said it, what they said, and at least one thing it is about | Thought |
| The above, plus what would count as an answer | Question |
| The above, plus what was chosen, at least one alternative passed over, and why | Decision |

If a field cannot be filled from what the person said, the claim is the simpler kind. A proposal with nothing chosen is a thought. A question with options listed and no choice made is a question.

Run `check(claim, Kind)` when unsure. It returns a report and does not raise on a claim that falls short.

## Record honestly

- Keep `body` verbatim. Put the reduction in the `assertion`.
- Never invent an alternative, a rationale, or a source to make a kind fit.
- Leave `modality` as `unstated` unless there is a sign of the speaker's footing. Set `basis` to `stated` when their own words carried it and `inferred` when you read it in.
- Set the record yourself: the author is the person you are working for, and `captured_from` is the call, document, or session. These are facts, not content for a model to write.

## Change by adding

- A thought that becomes a decision is a new claim. Call `promote(thought, Decision, ...)`. The thought stays as it was.
- A decision owes a `resolves` edge to a question. Look for an open question that matches before writing a new one.
- A different choice is a different decision. Link the new one to the old with `supersedes`.

## Read the report

| Field | Meaning | What to do |
|---|---|---|
| `missing` | It is not this kind | Ask for the fields, or store it as the kind it fits |
| `owed` | It is this kind, with an edge outstanding | Store it and tell the person what is owed |
| `unverified` | An edge points at a claim you did not supply | Pass it in `known` and check again |
| `revised` | Something it rests on has a newer version | Tell the person |

Report what you found in those terms. Do not present an incomplete claim as complete.

## Define a kind for someone

When a person describes a kind of their own, write it as a template and load it with `load_kinds`:

```yaml
risk:
  specializes: thought
  adds:
    likelihood: low|medium|high
    impact: text
```

Every kind names the kind it specializes. Give it at least one required field, or structure cannot tell it from its parent. Add fields; never redefine one the parent already has. Use `requires` sparingly.

## Verify

Build one real claim of the new kind and run `check` on it. Confirm `to_yaml` of the loaded kind matches the template you wrote.
