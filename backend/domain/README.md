# domain

The dataset in memory, read-only, loaded once.

| File | Role |
|---|---|
| `sources.py` | `read_json(path)`: the only code that knows where data comes from |
| `records.py` | `Pokemon`, `Move`, `Ability`, `Type`, `Stats` (dataclasses), `DamageClass`. `from_json` is the only code reading JSON keys; units become m and kg |
| `repository.py` | `Kind`, `EntityRef(kind, name)`, `Repository`: lookups by name, `by_kind`, `pokemon_by_type`, `moves_by_type`, `pokemon_with(ref)`, `evolution_family(name)` |

- **Attributes, not string keys**: `move.power`, `pokemon.stats.special_attack`. mypy catches a misspelt field
  or a forgotten `None` (a status move has no power). StrEnum keys wouldn't: mypy can't check a dict lookup
  whose key isn't a plain string.
- **Types** aren't records in the JSON: they come from Pokémon and move types (`Type(name)`).
- **Dataset order** is kept; only the ranking features sort.
- **No database**: 478 KB, never written. SQLite would stay inside `Repository`.
