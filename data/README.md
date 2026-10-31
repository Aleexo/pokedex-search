# data

| File | Content |
|---|---|
| `pokedex.json` | the provided dataset, unchanged (sha256 `251b7a02837bcb01…`): 151 Pokémon, 164 Gen 1 moves, 114 abilities |
| `type_chart.json` | multipliers between the 18 types (only those ≠ ×1), fetched once from PokeAPI. Refresh: `python scripts/fetch_type_chart.py` from `pokedex-search/` |

Caveats: moves are Gen 1 but abilities and types are modern; heights and weights are in decimetres and
hectograms (converted to m and kg on loading); sprites are remote URLs.
