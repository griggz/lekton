# lekton development guidelines

> **Audience**: coding agents and human developers working on this repository. To *use* lekton, read [`llms.txt`](llms.txt) and [`skills/lekton/SKILL.md`](skills/lekton/SKILL.md).

lekton is a small Python library (Python 3.10 or later, Pydantic v2) for defining kinds of claims from one primitive, the thought.

## Workflow

```bash
uv sync
```

```bash
uv run pytest
```

Run the tests before you call anything done. They also run every script in `examples/`.

## Repository structure

| Path | Contents |
|---|---|
| `lekton/` | The package. `thought.py` is the primitive, `kinds.py` the shipped kinds, `check.py` the structural check, `declare.py` the template format |
| `tests/` | pytest suite |
| `examples/` | Runnable scripts, one idea each |
| `docs/` | Markdown documentation |
| `skills/` | Skills for agents that use lekton |
| `assets/` | Logo files |
| `llms.txt` | Index of the docs for agents |

## What the library is for

It fixes the shape of a claim and reports what is missing. It does not police how carefully anyone uses it.

| | What the library does |
|---|---|
| Shape | Enforces it |
| Completeness | Reports it, never blocks |
| Diligence | Stays out of it |

Hold to this when you add anything. Do not add a strict mode, a quality score, or a check that rejects a claim for being incomplete.

## Rules

- **`check` is the authority.** A class name or a `kind` key is a label. Decide what a claim is by its structure.
- **A kind adds; it never redefines.** The library raises on a subclass that changes an inherited field. Keep it that way.
- **`Thought`, `Question`, and `Decision` are the opinionated core.** Do not change their fields without the maintainer's say.
- **Required edges are owed, not gates.** A missing edge belongs in `Report.owed`.
- **Defaults must not overclaim.** `modality` defaults to `unstated` for this reason.
- **Docs and examples must be true.** If you change behavior, update `docs/reference.md`, the README, and any example it touches. Add an example to `llms.txt` when you add one.
- **This is a public repository.** Do not add names of private projects, customers, or people.

## Code standards

- Type hints on everything public. The package ships `py.typed`.
- Comments say why, not what.
- Export public names from `lekton/__init__.py` and list them in `__all__`.
- Test names read as sentences: `test_a_decision_without_a_question_is_a_decision_that_owes_one`.

## Commits and pull requests

- Conventional commit messages: `feat:`, `fix:`, `docs:`, `chore:`.
- Work on a branch and open a pull request into `main`.
