# backend

Python 3.11+, FastAPI, managed with uv. One process serves the API and the built frontend.

```bash
uv sync --extra dev                    # once
uv run pytest                          # tests, docstring examples, mypy
uv run uvicorn api.main:app --reload   # http://localhost:8000 (interactive API docs: /docs)
```

| Folder | Role |
|---|---|
| [`domain/`](domain/README.md) | typed records (dataclasses) and the in-memory `Repository` |
| [`search/`](search/README.md) | normalisation, edit distance, ranking of names |
| [`explore/`](explore/README.md) | ranking Pokémon or moves on one field, alone or by type |
| [`coverage/`](coverage/README.md) | type chart and coverage moves |
| [`api/`](api/README.md) | FastAPI routes; also serves `frontend/dist` |
| [`tests/`](tests/README.md) | unit, API and labelled-case tests, and mypy |

- **Features don't depend on FastAPI**: `SearchEngine.from_data().search("bulbi")` works in a Python shell; the API
  only shapes JSON.
- **Typed**: records are dataclasses and kinds / fields are enums; mypy runs inside the tests.
- **No database**: the data (478 KB, read-only) is loaded once into memory.
- Every function has a docstring with a runnable example; the examples run with the tests.
