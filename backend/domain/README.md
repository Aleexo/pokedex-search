# domain

The dataset in memory, read-only, loaded once.

| File | Role |
|---|---|
| `sources.py` | `read_json(path)`: the only code that knows where data comes from |
| `records.py` | `Kind`, `EntityRef(kind, id, name)` (an entity's identity: kind and id; the name for display), `TYPE_IDS` (PokeAPI's type numbers), `Entity` (kind, id, name, `.ref`) and its four records `Pokemon`, `Move`, `Ability`, `Type`; `Stats`, `DamageClass`. `from_json` is the only code reading JSON keys; units become m and kg |
| `repository.py` | `Repository`: lookups by name (`by_kind`, `ref(kind, name)`) and by id (`by_id`, `get(ref)`); `linked(ref, kind)`: the links (`LINKS`, `can_link`), built once at load as refs, Pokémon in Pokédex order; `evolution_family(ref)` |

- **Attributes, not string keys**: `move.power`, `pokemon.stats.special_attack`. mypy catches a misspelt field
  or a forgotten `None` (a status move has no power). StrEnum keys wouldn't: mypy can't check a dict lookup
  whose key isn't a plain string.
- **`EntityRef` and `Entity`**: the ref is the identity, **kind and id** (move 94 and type 14 are both `psychic`):
  equality, hashing and order ignore the name, which is carried for display. Names stay at the edges (API, URLs,
  YAML cases), turned into refs once by `repo.ref(kind, name)`. The record is the data; `record.ref` gives its identity.
- **Type numbers**: the data has none, so types take PokeAPI's (`TYPE_IDS`: Normal 1 … Fairy 18).
- **Types** aren't records in the JSON: they come from Pokémon and move types (`Type(id, name)`, numbered from `TYPE_IDS`).
- **Dataset order** is kept; only the ranking features sort.
- **No database**: 478 KB, never written. SQLite would stay inside `Repository`.
