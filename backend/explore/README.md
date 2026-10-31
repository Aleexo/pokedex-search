# explore

Ranks Pokémon or moves on one field, alone or by type. Rules: [docs/EXPLORE.md](../../docs/EXPLORE.md).

```python
from explore import Explorer, Number
Explorer(repo).ranked(Number.SPEED, by_type=True)[:8]   # 8 fastest types
Explorer(repo).ranked(Number.POWER)[:8]                 # 8 most powerful moves
```

All in `explorer.py`:

| Name | Role |
|---|---|
| `Number` | the 12 fields; `Number.subject` says whether it ranks Pokémon or moves |
| `Subject`, `Order` | Pokémon / moves; top / bottom |
| `Explorer` | `pokemon(types)`, `moves(types)` (type filter), `rows`, `ranked` |
| `tied_beyond` | rows cut at the 8th that tie with it |
