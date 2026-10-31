# tests

```bash
uv run pytest             # from backend/: tests, docstring examples, mypy
uv run pytest -k typos    # a subset
```

Docstring examples (`>>>`) in every module run as tests; `backend/conftest.py` gives them `repo`, `engine`,
`explorer`, `advisor`…

| File | Covers |
|---|---|
| `test_resolver.py` | the labelled cases in `cases/resolver.yaml` |
| `test_normalize.py` | normalisation, OSA distance |
| `test_engine.py` | ranking, reasons, notes |
| `test_explore.py` | ranking, averages, moves, type filter, ties |
| `test_coverage.py` | type chart, walls, coverage lists, edge cases, rules on all 151 Pokémon |
| `test_api.py` | every route, 404 / 422 |
| `test_repository.py` | records, units, `by_kind` |
| `test_types.py` | runs mypy |

## Adding a search case

One line in `cases/resolver.yaml`, no code:

```yaml
typos:
  - {query: pikchu, expect: "pokemon:pikachu"}
several:
  - {query: psychic, expect: ["type:psychic", "move:psychic"]}
```

A single `expect` must be the first hit; a list must all be present. Every wrong result found by hand
should become a case.
