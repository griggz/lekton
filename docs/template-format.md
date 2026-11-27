# Template format

A template is a YAML file that declares kinds of claims. The format is the standard. The kinds in it are yours.

`load_kinds` builds working kinds from a template with no code. `to_yaml` writes a kind back out in the same format.

## A kind

```yaml
decision:
  specializes: thought
  parts:
    passed_over: thought
  requires:
    because: thought
    resolves: question
```

The top-level key is the kind's name, in `snake_case`. A kind has up to four sections:

| Key | Required | Meaning |
|---|---|---|
| `specializes` | Yes | The parent kind. The new kind is everything its parent is |
| `adds` | No | Fields the kind adds to its parent |
| `parts` | No | Other claims the kind is made of, by the role each plays |
| `requires` | No | Edges the kind owes to other claims |

Any other key is an error, so a misspelling cannot load a kind with less than you meant. Kinds load in the order they appear, so a later kind can name an earlier one.

## A template stands on its own

A kind depends on its parent, on the kinds that fill its roles, and on the kinds its owed edges point at. A decision depends on a question. A template that names a kind it does not declare, and that the loader does not already know, is an error that says which edge points where.

`to_yaml` writes a template closed by default: the kinds you ask for plus everything they depend on, each after what it needs, so `to_yaml(Decision)` declares `question` first. Pass `closed=False` to write only the kinds named.

A template that declares a kind the loader already has, the same way, is importing it: the loader hands back the kind it knows instead of building a second one. The shipped kinds live in `lekton/kinds.yaml` in this format, so a template of your own can name `question` and `decision` without declaring them. The same name with a different shape is refused.

## Fields

Each entry under `adds` is a field name and a type.

| Type | Written | Example value |
|---|---|---|
| Text | `text` | `"Retire it"` |
| Whole number | `integer` | `3` |
| Number | `number` | `0.8` |
| True or false | `boolean` | `true` |
| Date | `date` | `2026-11-24` |
| Date and time | `datetime` | `2026-11-24T14:30:00Z` |
| List | `[text]` | `["Port it", "Replace it"]` |
| Choice | `low\|medium\|high` | `"low"` |

A field is required unless it is marked optional with `?`:

- On the type for a plain value: `owner: text?`
- On the name for a list: `tags?: [text]`

A required text or list field must not be empty. An empty value counts as missing.

## Made of other claims

```yaml
bet:
  specializes: thought
  adds:
    thesis: text
  parts:
    backs: decision
    exposed_to: risk
```

Each entry under `parts` is a role and the kind that fills it. The role is a verb, and it is the edge on the claim: a bet carries a `backs` edge to a decision and an `exposed_to` edge to a risk. A role is filled by at least one claim of its kind; without one the claim is not this kind, and `check` lists the role in `missing`.

A role that needs more than one claim says how many:

```yaml
pattern:
  specializes: thought
  parts:
    seen_in: {kind: thought, min: 2}
```

`min` is the fewest claims of that kind the role takes. Leave it out for one. A pattern recurs, so it is seen in at least two claims; with one sighting `check` reports the role missing with the count it found.

A composite is still a thought. It has its own author, date, and things it is about. Its parts stay as they are, and each edge records the version the part was at.

**Field or part?** A field is about the claim itself: how likely, how bad, what would settle it. Something someone could disagree with on its own is a claim of its own, and belongs in a role, where it keeps its author and can be contradicted later without touching the claim that points at it. That is why a decision has no `rationale` field and a `because` role instead.

YAML reads a bare `on`, `off`, `yes`, or `no` as a boolean. Quote a verb spelled that way, or pick another word. `to_yaml` quotes them for you.

## Owed edges

```yaml
requires:
  resolves: question
```

Each entry is a verb and the kind the edge must point at. An owed edge is a completeness check, not a gate. A decision with no question is still a decision; `check` reports it as fitting and incomplete. Keep these rare.

## Rules

1. Every kind names a parent that is already defined. Only the thought has no parent, and it is not loaded from a template.
2. A kind adds fields. It cannot redefine one it inherits.
3. A composite names at least one role. Roles and owed edges are inherited and added to, never dropped.
4. A kind should add at least one required field, or declare a role of its own. A kind that adds only optional fields has the same shape as its parent, so structure cannot tell the two apart and `qualifies` and `read` will never pick it.

## The thought

Every kind descends from this. It is built into the library and printed here for reference.

```yaml
thought:
  id: text
  record:
    author: text
    recorded_at: datetime
    captured_from: text?
    version: integer
  body: text
  about:
  - thing: text
    role: subject|object?
  assertion?:
    predicate: text
    value: text?
    polarity: +|-
    modality: asserted|hypothesis|forecast|reported|unstated
    basis: stated|inferred?
    valid_at: date?
  sourced_from?: [text]
  links?:
  - verb: text
    to:
      id: text
      version: integer
      graph: text?
    basis: stated|inferred?
    by: text?
```

| Group | What it holds |
|---|---|
| `record` | Facts about the claim: who, when, out of what, which version. Not arguable |
| `body` | What was said, verbatim |
| `about` | Everything the claim touches. At least one thing |
| `assertion` | Optional. The body reduced to one statement someone can agree or disagree with |
| `sourced_from` | Evidence the claim rests on. It can go stale |
| `links` | Edges to other claims. The verb is a role from `parts`, an edge from `requires`, or `evolved_from` and `supersedes`, which any claim may carry. `basis` says whether the speaker drew the edge or a reader inferred it; `by` says who, when it was not the author |

## What the format cannot say yet

- A mood. An instruction or a practice is a claim with no truth value, and the assertion's modality only says how sure the speaker is that something is so.
- Default values and numeric ranges.
- Reference types such as a person or a thing. They are `text` for now.
- Which field carries a kind's identity.
- A namespace or a version for the kind itself.
