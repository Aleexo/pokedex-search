# coverage

A Pokémon's moves of other types that get past its walls: ×2 first, then ×1. Rules: [docs/MOVE_COVERAGE.md](../../docs/MOVE_COVERAGE.md).

```python
from coverage import CoverageAdvisor, TypeChart
report = CoverageAdvisor(repo, TypeChart.from_data()).suggest("charizard")
report.walls      # ['rock']
report.moves[0]   # Earthquake: physical (Attack 84), hits 1 wall x2 (hits=1, neutral=0)
```

| File | Role |
|---|---|
| `type_chart.py` | `TypeChart.multiplier(attack, defend)`, from `data/type_chart.json` |
| `coverage.py` | `CoverageAdvisor.suggest(name)` → `CoverageReport` (walls, moves, notes) |
