# api

Thin FastAPI layer: it shapes JSON and serves the frontend. Run from `backend/`:
`uv run uvicorn api.main:app --reload`, then http://localhost:8000 (interactive docs: `/docs`).

| Route | Returns | Errors |
|---|---|---|
| `GET /api/search?q=…&page=1` | one page of ranked hits (20 per page), each with its reason, types and, for a Pokémon, a summary; a relation query (`poison moves`) also gives `groups` (each list's heading and count), `group` on each hit, and all its rows on one page | 422, 404 past the end |
| `GET /api/pokemon?page=1` | all Pokémon in Pokédex order, same paged shape as a search (`query` is empty) | 404 past the end |
| `GET /api/entity/{kind}/{name}` | details for the panel; each Pokémon or move named comes with what its hover card shows | 422 kind, 404 name |
| `GET /api/explore?x=…[&by_type=true]&order=top[&types=…]` | up to 8 rows, counts, ties beyond the 8th | 422 |
| `GET /api/explore/fields` | fields with labels and subject, filter types | |
| `GET /api/coverage/{name}` | walls, up to 5 coverage moves, notes | 404 |
| `GET /` | the frontend, with `Cache-Control: no-cache` | |

Each search logs one line: `query='char' hits=4 top=[...] ms=0.8`.
