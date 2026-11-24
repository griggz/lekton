# Template format

A template is a YAML file that declares kinds of claims. The format is the standard. The kinds in it are yours.

`load_kinds` builds working kinds from a template with no code. `to_yaml` writes a kind back out in the same format.

## A kind

```yaml
decision:
  specializes: thought
  adds:
    chosen: text
    alternatives: [text]
    rationale: text
  requires:
    resolves: question
```

The top-level key is the kind's name, in `snake_case`. A kind has up to four parts:

| Key | Required | Meaning |
|---|---|---|
| `specializes` | Yes | The parent kind. The new kind is everything its parent is |
| `adds` | No | Fields the kind adds to its parent |
| `composed_of` | No | Other claims the kind is made of |
| `requires` | No | Edges the kind owes to other claims |

Kinds load in the order they appear, so a later kind can name an earlier one.

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
  composed_of:
    min: 2
    parts: [decision, risk]
  adds:
    thesis: text
```

| Key | Meaning |
|---|---|
| `min` | Fewest parts in total. Never less than 2 |
| `parts` | Kinds it must contain, at least one claim of each |
| `allows` | Kinds a part may be. Leave it out to allow any claim |

A composite is still a thought. It has its own author, date, and things it is about. Its parts stay as they are, and each `composed_of` edge records the version the part was at.

## Owed edges

```yaml
requires:
  resolves: question
```

Each entry is a verb and the kind the edge must point at. An owed edge is a completeness check, not a gate. A decision with no question is still a decision; `check` reports it as fitting and incomplete. Keep these rare.

## Rules

1. Every kind names a parent that is already defined. Only the thought has no parent, and it is not loaded from a template.
2. A kind adds fields. It cannot redefine one it inherits.
3. A composite has two or more parts.
4. A kind should add at least one required field, or be made of parts. A kind that adds only optional fields has the same shape as its parent, so structure cannot tell the two apart and `qualifies` and `read` will never pick it.

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
```

| Group | What it holds |
|---|---|
| `record` | Facts about the claim: who, when, out of what, which version. Not arguable |
| `body` | What was said, verbatim |
| `about` | Everything the claim touches. At least one thing |
| `assertion` | Optional. The body reduced to one statement someone can agree or disagree with |
| `sourced_from` | Evidence the claim rests on. It can go stale |
| `links` | Edges to other claims: `resolves`, `composed_of`, `evolved_from`, `supersedes` |

## What the format cannot say yet

- Default values and numeric ranges.
- Reference types such as a person or a thing. They are `text` for now.
- Which field carries a kind's identity.
- A namespace or a version for the kind itself.
