# lekton

Claim kinds built from one primitive.

A thought is the primitive. Every other kind of claim is a thought plus something, and there are only three ways to add:

| Relation | Meaning | In code |
|---|---|---|
| is-a | The kind adds fields to its parent and never removes any | Subclass it |
| made-of | The kind is composed of two or more other claims | `composed_of(...)` |
| requires | The kind owes an edge to another claim | `requires(...)` |

The name is Stoic. A *lekton* is "what can be said": the content of an utterance, apart from its words. The Stoics sorted lekta into kinds (assertions, questions, commands) about 2,300 years ago.

Status: v0. Not on PyPI yet.

## What this library is for

It gives you building blocks. It does not police how you use them.

| | What the library does | Example |
|---|---|---|
| Shape | Enforces it | A thought is about at least one thing. A composite has two or more parts |
| Completeness | Reports it, never blocks | A decision with no question is `owed`, not rejected |
| Diligence | Stays out of it | Whether your extractor worked hard on modality |

The library makes claims comparable. Whether they are good is up to the system you build around it. There is no strict mode, on purpose.

## A thought

```python
from lekton import Thought, Question, Decision, Record, Assertion

thought = Thought(
    record=Record(author="wayne", captured_from="working session"),
    body="I do not think I ever use the traverse tool.",
    about=[{"thing": "traverse tool", "role": "subject"}, "Postgres port"],
    assertion=Assertion(
        predicate="is never used by me", modality="hypothesis", basis="stated"
    ),
)
```

- `record` holds facts about the thought: who, when, out of what, which version. Nobody has to agree with a claim to agree on its record.
- `body` is what was said, verbatim.
- `about` is everything it touches. There must be at least one.
- `assertion` is optional: the body reduced to one statement someone can agree or disagree with.

### Modality

An assertion carries the speaker's footing. The statement stays the same; the footing changes how much weight it can bear.

| Modality | The footing |
|---|---|
| `asserted` | I am telling you it is so |
| `hypothesis` | My guess, not checked |
| `forecast` | About the future; nobody can check it yet |
| `reported` | Someone else's word, passed along |
| `unstated` | Nobody said, and it could not be told. The default |

`unstated` is the default so that a claim nobody examined never passes as a firm one. A question's assertion stays `unstated`: nothing is asserted until its blank is filled.

`basis` says how the modality is known: `stated` when the speaker's own words carried it ("I think", "Dave told me"), `inferred` when whoever recorded the claim read it in. An `unstated` modality has no basis.

Modality is not confidence. It is the kind of footing, not how sure the speaker is.

## Your own kinds

```python
from lekton import composed_of

class Risk(Thought):                 # is-a
    likelihood: str
    impact: str

class Bet(Thought):                  # made-of
    thesis: str
    parts = composed_of(Decision, Risk)
```

`Question` and `Decision` ship with the library because we hold an opinion about what they are. Everything else is yours to define.

## Structure decides, not the label

`check` reports what a claim is by what it carries. It never raises on a claim that falls short.

```python
from lekton import check, promote

decision = promote(
    thought, Decision,
    chosen="Retire it, with no replacement",
    alternatives=["A read-only SQL tool with the same gating"],
    rationale="Unused, and already off on shared instances.",
)

report = check(decision)
report.fits        # True: it names a choice and an alternative
report.complete    # False
report.owed        # ('resolves: question',)
```

A report separates four things:

| Field | Meaning |
|---|---|
| `missing` | Fields or parts it lacks. Without them it is not this kind |
| `owed` | Required edges not in place. It is this kind, but incomplete |
| `unverified` | Edges that exist but point at claims that could not be looked up |
| `revised` | Linked claims that now have a newer version than the one pinned |

Related functions:

- `promote(thought, Kind, **adds)` makes a new claim with its own record and an `evolved_from` edge. The thought is left alone.
- `qualifies(claim)` returns the most specific kinds a claim's structure fits.
- `read(data)` builds a claim as the most specific known kind. A kind this process has never seen comes back as its nearest known ancestor, extra fields intact.
- `status(question, claims)` returns `open` or `answered`. It is worked out from edges every time and never stored.

## Kinds as data

A kind can be written out as a template and built back from one, with no code.

```python
from lekton import to_yaml, load_kinds

print(to_yaml(Question, Decision))
```

```yaml
question:
  specializes: thought
  adds:
    settled_by: text
    owner: text?
decision:
  specializes: thought
  adds:
    chosen: text
    alternatives: [text]
    rationale: text
  requires:
    resolves: question
```

```python
built = load_kinds("""
hazard:
  specializes: thought
  adds:
    likelihood: low|medium|high
    impact: text
""")
Hazard = built["hazard"]
```

Types: `text`, `integer`, `number`, `boolean`, `date`, `datetime`, a list `[text]`, or a choice `a|b|c`. A trailing `?` marks a field optional. A required text or list field must not be empty.

## Rules the library enforces

1. A claim is about at least one thing.
2. A kind adds to its parent. Redefining an inherited field is an error.
3. A composite has two or more parts.
4. A required edge is a completeness check, not a gate. A decision with no question is still a decision.
5. A kind that adds nothing required cannot be told from its parent by structure, so `qualifies` and `read` never guess it.
6. An `unstated` modality carries no basis.

## Not here yet

- Storage, a graph, or an MCP server. This is the model layer only.
- Versioning beyond the pin on an edge.
- Namespaces for kinds, and versions of a kind's own definition.
- Reference types (`person`, `thing`, `source`). They are plain text for now.

## Development

```bash
uv sync
```

```bash
uv run pytest
```

## License

Apache-2.0. See [LICENSE](LICENSE).
