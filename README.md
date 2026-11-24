<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
    <img src="assets/logo-light.svg" alt="lekton: what can be said" width="400">
  </picture>
</p>

# lekton

Claim kinds built from one primitive.

A thought is the primitive. Every other kind of claim is a thought plus something, and there are only three ways to add:

| Relation | Meaning | In code |
|---|---|---|
| is-a | The kind adds fields to its parent and never removes any | Subclass it |
| made-of | The kind is composed of two or more other claims | `composed_of(...)` |
| requires | The kind owes an edge to another claim | `requires(...)` |

The name is Stoic. A *lekton* is "what can be said": the content of an utterance, apart from its words. The Stoics sorted lekta into kinds (assertions, questions, commands) about 2,300 years ago.

The mark is a lambda, the first letter of λεκτόν, drawn as two strokes: a thought, and what you add to it.

Status: v0. Not on PyPI yet.

## Background

`lekton` makes the nodes of a knowledge graph easier to define, generate, and curate. It treats claims as separate from things. A person, a company, or a tool is a thing. What someone decided or believed about it is a claim. Every claim is about at least one thing, and every claim has an author and a time.

Things already have standards. schema.org and Wikidata describe people, organizations, and places, and individual fields keep their own ontologies, such as the Open Energy Ontology for energy systems. Those standards exist because the world mostly agrees on what a person or a power plant is.

I have not found an open standard for how to structure a claim. Nanopublications, Wikidata's statement model, and PROV-O cover who said something and when. Nothing covers the kinds. Claims are more complex than things, and one person structures a claim differently than the next.

So `lekton` builds claims in layers of abstraction. A thought is the most basic claim. The first layer above it holds kinds that add something to a thought, such as a question or a decision. Layers above that combine kinds from the first, so one claim can be made of others.

The open work is defining that first layer: which kinds belong in it, and what each one adds. The library ships a question and a decision as the start.

Everything past the first layer should become standard by adoption, not decree. Nobody decreed schema.org. Usage made it the standard.

The longer argument is in [From Knowledge to Context](https://griggz.com/writing/from-knowledge-to-context).

## What this library is for

It gives you the building blocks to programmatically define the kinds of claims you make.

- **Compose.** A person or an agent can build a kind from a few parts, then build larger kinds out of those, until they have an ontology of claims.
- **Deconstruct.** Any kind can be taken apart into its parent, the fields it adds, the claims it is made of, and the edges it owes. That includes someone else's, so you can see what makes their ontology theirs.
- **Test.** A kind is structure, so a claim can be checked against it in code. You can write tests against your claims.

It does not police how you use them.

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

## For agents

lekton is meant to be picked up by an agent working for a person, as much as by the person.

| If you are | Start here |
|---|---|
| An agent that needs the docs | [`llms.txt`](llms.txt), an index of every page as Markdown |
| An agent recording claims for someone | [`skills/lekton/SKILL.md`](skills/lekton/SKILL.md) |
| Wiring lekton into tool calls or structured output | [Using lekton from an agent](docs/agents.md) |
| Working on this repository | [`AGENTS.md`](AGENTS.md) |

More in [`docs/`](docs/), and runnable scripts in [`examples/`](examples/).

## Development

```bash
uv sync
```

```bash
uv run pytest
```

## License

Apache-2.0. See [LICENSE](LICENSE).
