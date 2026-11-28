# API reference

Everything below imports from the top level: `from lekton import ...`.

## Models

All are Pydantic v2 models, so `model_validate`, `model_dump`, and `model_json_schema` work on them.

### `Thought`

The primitive. Subclass it to make a kind.

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | Generated if not given |
| `record` | `Record` | Required |
| `body` | `str` | Required, not empty |
| `about` | `list[About]` | Required, at least one. A plain string is read as a thing |
| `assertion` | `Assertion \| None` | Optional |
| `sourced_from` | `list[str]` | Defaults to empty |
| `links` | `list[Link]` | Defaults to empty |

Unknown fields are kept, not dropped. That is how a kind this process has never seen survives a round trip.

| Member | Returns | Meaning |
|---|---|---|
| `Thought.kind_name()` | `str` | The kind's name. `OpenQuestion` is `open_question` |
| `Thought.parent()` | kind or `None` | The kind this one specializes |
| `Thought.adds()` | `dict` | The fields this kind adds to its parent |
| `Thought.composition()` | `dict[str, Role]` | Parts, verb to role. A `Role` has `kind` and `min`. Inherited. Empty for a kind with no parts |
| `Thought.requirements()` | `dict[str, kind]` | Owed edges, verb to target kind. Inherited |
| `Thought.depends_on()` | `list[kind]` | The kinds this one cannot be declared without: its parent, its parts' kinds, its owed edges' kinds |
| `Thought.is_distinct()` | `bool` | Whether structure can tell this kind from its parent |
| `claim.kind` | `str` | Same as `kind_name()`, on an instance |
| `claim.ref()` | `Ref` | A pointer to this claim at its current version |
| `claim.with_link(verb, to, *, basis=None, by=None)` | claim | A copy with one more edge. The original is unchanged |
| `claim.linked(verb)` | `list[Ref]` | Targets of this claim's edges with that verb |

Defining a subclass that redefines an inherited field raises `TypeError`.

### `Question`

A thought plus `settled_by: str` (required) and `owner: str | None`. It has no status field. See `status`.

### `Decision`

A thought that adds no fields. It is made of `passed_over: Thought` (at least one alternative, each a claim of its own) and owes `because: Thought` and `resolves: Question`. What was chosen is its own `body`.

### `Record`

| Field | Type | Default |
|---|---|---|
| `author` | `str` | Required |
| `recorded_at` | `datetime` | Now, in UTC |
| `captured_from` | `str \| None` | `None` |
| `version` | `int` | `1` |

### `About`

`thing: str` and `role: "subject" | "object" | None`. A role is only allowed when the claim has an assertion.

### `Assertion`

| Field | Type | Default |
|---|---|---|
| `predicate` | `str` | Required |
| `value` | `str \| None` | `None` |
| `polarity` | `"+" \| "-"` | `"+"` |
| `modality` | `"asserted" \| "hypothesis" \| "forecast" \| "reported" \| "unstated"` | `"unstated"` |
| `basis` | `"stated" \| "inferred" \| None` | `None` |
| `valid_at` | `date \| None` | `None` |

An `unstated` modality with a basis is refused.

### `Ref` and `Link`

`Ref` is `id: str`, `version: int`, `graph: str | None`.

| `Link` field | Type | Default |
|---|---|---|
| `verb` | `str` | Required |
| `to` | `Ref` | Required |
| `basis` | `"stated" \| "inferred" \| None` | `None` |
| `by` | `str \| None` | `None` |

The verb is a role the kind declares in `composed_of`, an edge it owes in `requires`, or one of the two any claim may carry: `evolved_from` and `supersedes`. `basis` says how the edge is known, with the same words an assertion uses; `by` names who drew it when that is not the claim's author. Both default to nothing claimed. A `Link` keeps fields it does not know, so a graph that scores its edges carries the score there; the library has no scale of its own.

## Declaring relations

| Call | Use |
|---|---|
| `composed_of(**roles)` | Class attribute on a kind made of other claims, verb to kind. A role is a kind, or `(kind, n)` for one that takes at least n claims: `composed_of(passed_over=Thought)`, `composed_of(seen_in=(Thought, 2))` |
| `Role(kind, min=1)` | What `composition()` returns for each verb. `min` below 1 raises `ValueError` |
| `requires(**edges)` | Class attribute on a kind that owes an edge, for example `requires(resolves=Question)` |

Both map a verb to a kind, and the verb is the edge on the claim. They differ in what a missing edge means: a part missing puts the claim in `Report.missing` (it is not this kind); a required edge missing puts it in `Report.owed` (it is this kind, incomplete). Both are inherited and added to; a subclass never drops one. `composed_of` with no roles raises `ValueError`.

```python
class Bet(Thought):
    thesis: str
    parts = composed_of(backs=Decision, exposed_to=Risk)
```

## Checking

### `check(claim, kind=None, *, known=()) -> Report`

Checks a claim against a kind by its structure. `claim` is a `Thought` or a plain mapping. `kind` defaults to the claim's own class, or `Thought` for a mapping. `known` is the claims that edges can be looked up in: an iterable, or a mapping of id to claim.

It does not raise when a claim falls short. A `kind` key in a mapping is ignored, because a label is not evidence.

### `Report`

| Field | Meaning |
|---|---|
| `kind` | The kind checked against |
| `missing` | Fields or parts the claim lacks. Without them it is not this kind |
| `owed` | Required edges not in place. It is this kind, but incomplete |
| `unverified` | Edges that exist but point at claims not found in `known` |
| `revised` | Linked claims that now have a newer version than the one pinned |
| `detail` | The reason behind each `missing` entry |
| `fits` | `True` when nothing is missing |
| `complete` | `True` when it fits, owes nothing, and nothing is unverified |

### `qualifies(claim, *, kinds=None, known=()) -> list[kind]`

The most specific kinds the claim's structure fits. Empty if it is not a valid thought. `kinds` defaults to every kind defined in the process.

### `read(data, *, kinds=None, known=()) -> Thought`

Builds a claim as the most specific known kind its structure fits. A kind this process has never seen comes back as its nearest known ancestor with its extra fields intact. Raises `pydantic.ValidationError` if the data is not a thought.

### `promote(thought, kind, *, author=None, captured_from=None, **adds) -> claim`

Makes a new claim of a more specific kind. The new claim has its own id and record, carries the thought's content, and links back with `evolved_from`. Pass the fields the kind adds, if any, as keyword arguments; pass an existing field again to override it. Parts are edges, so add them afterwards with `with_link`.

Raises `pydantic.ValidationError` if the added fields do not satisfy the kind, and `TypeError` if `kind` does not specialize the thought's own kind. It does not check parts or owed edges. Run `check` on the result.

### `resolved_by(question, known) -> list[Thought]`

The claims in `known` that resolve the question and still stand. A claim stands until another claim supersedes it.

### `status(question, known) -> "open" | "answered"`

Worked out from edges every time. Never stored.

## Kinds as data

| Call | Returns |
|---|---|
| `declare(kind)` | The kind as a plain dict in the [template format](template-format.md) |
| `closure(*kinds)` | The kinds given plus every kind they depend on, in an order that loads. The thought is left out |
| `to_yaml(*kinds, closed=True)` | One or more kinds as a YAML template. Closed by default: a decision brings the question it resolves, so the template stands alone. `closed=False` writes only the kinds named |
| `load_kinds(source, *, kinds=None)` | A dict of name to kind, built from a YAML string or a dict |
| `load_kind(source, *, kinds=None)` | The single kind a template declares |
| `kinds()` | Every kind defined in the process, by name |

A kind the process already knows, declared the same way, is reused rather than built again: loading the shipped template hands back `Question` and `Decision` themselves. The same name with a different declaration is an error, since there are no namespaces yet.

`load_kinds` raises `ValueError` for an unknown parent, a missing `specializes`, an unknown type, a key the format does not know, a part or owed edge that points at a kind not declared or known (a decision needs its question), a name already defined with a different shape, or a verb that did not come through as text (YAML reads a bare `on`, `off`, `yes`, or `no` as a boolean; quote it), and `TypeError` for a field that redefines an inherited one.

The shipped kinds are also in the template format at `lekton/kinds.yaml`, and the test suite holds that file and `kinds.py` to the same declaration.
