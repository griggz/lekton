---
name: lekton
description: Record, check, or define kinds of claims (thoughts, questions, decisions, and a person's own kinds) with the Python lekton library, on behalf of the person whose thinking it is.
---

# Working with claims in lekton

A claim is something a person decided, noticed, argued, or believed. lekton gives every claim one base shape, the thought, and builds every other kind by adding to it. You are usually doing this for someone else, so the job is to record what they said, not what would make a tidier record.

## Find the current API

Check the installed version of `lekton`. Read [the documentation index](https://raw.githubusercontent.com/griggz/lekton/main/llms.txt) and the pages it links for what you need. The API reference lists every public name with its arguments and result.

## First, is it a claim at all?

A claim is content someone put into words that is about things and can be taken up: agreed with or disputed, answered, followed or refused. A thing has an identity and is pointed at: a person, a tool, a team, a report, a process with steps. A thing may have an author; it still cannot be disputed, only what is said about it can. Things go in `about`; claims carry a `record`. "The onboarding process" is a thing. "The onboarding process wastes a step" is a claim about it. Do not record a thing as a claim because it was mentioned.

An instruction ("send the agenda the day before") is a claim, but the library cannot yet mark it as one by structure. Record it as a thought with the instruction as its `body`, and do not give it an assertion as if it were a statement of fact.

## Pick the kind by what the claim carries

Decide by structure, not by how the claim sounds.

| If you can fill in | It is a |
|---|---|
| Who said it, what they said, and at least one thing it is about | Thought |
| The above, plus what would count as an answer | Question |
| The above, where the body is the commitment, plus at least one alternative passed over, recorded as a claim of its own | Decision |

A decision adds no fields. Its alternatives are claims linked with `passed_over`, its reason is a claim linked with `because`, and the question it answers is linked with `resolves`. If nothing was passed over, the claim is a thought. A question with options listed and no choice made is a question.

Run `check(claim, Kind)` when unsure. It returns a report and does not raise on a claim that falls short.

## Record honestly

- Keep `body` verbatim. Put the reduction in the `assertion`.
- Never invent a claim to fill a role, or a source to make a kind fit. A decision with no reason given owes one; record that it is owed.
- Record each part as its own claim with the person's words in its `body`. The reason for a decision is a claim someone can contradict later, not a field.
- Leave `modality` as `unstated` unless there is a sign of the speaker's footing. Set `basis` to `stated` when their own words carried it and `inferred` when you read it in.
- Set the record yourself: the author is the person you are working for, and `captured_from` is the call, document, or session. These are facts, not content for a model to write.

## Change by adding

- A thought that becomes a decision is a new claim. Call `promote(thought, Decision, body=...)`, then link each alternative with `with_link("passed_over", ...)` and the reason with `with_link("because", ...)`. The thought stays as it was.
- On every edge you draw, set `basis`: `stated` when the person's words connected the two claims, `inferred` when you did, and `by` to yourself when you inferred it. Never leave an edge you inferred looking like one the person drew.
- Pass the parts in `known` when you run `check`, or the report will say they are unverified.
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

Every kind names the kind it specializes, and declares only what it adds: `thought`, `question`, and `decision` ship with the library, so name them without declaring them. A kind that points at another kind depends on it; a template that uses `decision` must have `question` in reach, and the loader says so if not. `to_yaml` writes a template closed, so what you write out stands alone. Give a kind at least one required field or one role under `parts`, or structure cannot tell it from its parent. Add fields; never redefine one the parent already has. Use `requires` sparingly.

A field is about the claim itself, such as a likelihood or what would settle it. Anything someone could disagree with on its own is a claim, and goes in a role, not a field. A role that needs more than one claim says so: `seen_in: {kind: thought, min: 2}` for a kind that recurs. Do not spell a role `on`, `off`, `yes`, or `no` without quotes; YAML reads those as booleans.

## Verify

Build one real claim of the new kind and run `check` on it. Confirm `to_yaml` of the loaded kind matches the template you wrote.
