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
| `test_relations.py` | the labelled cases in `cases/relations.yaml` and that the file is what the script writes; hits and their lists |
| `test_normalize.py` | normalisation (`search/names`), the OSA distances the resolver relies on |
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

A relation case is added to `CASES` in `scripts/relation_cases.py`, which computes the expected lists from the
data on its own and writes `cases/relations.yaml`:
`uv run --directory backend python ../scripts/relation_cases.py` from `pokedex-search/` (a test fails if the file
and the script disagree). Each case lists the expected lists in order (or `none`, or `unchanged` when there is no
kind word), each with its heading, count and items (all, or the first ones as `starts`):

```yaml
one_filter:
  - query: charizard abilities
    expect:
      - {title: "Abilities of Charizard", count: 2, items: [ability:blaze, ability:solar-power]}
```
