# search

Search over Pokémon, moves, abilities and types, in two parts.

```python
from search import SearchEngine
SearchEngine.from_data().search("bulbi")   # Bulbasaur, "Close to 'bulbi' (possible typo)"
```

| Path | Role |
|---|---|
| [`names/`](names/README.md) | The name search: the closest names, OSA edit distance ([docs/SEARCH.md](../../docs/SEARCH.md)) |
| `relations/` | The relation search: `poison moves`, `fire pokemon ability blaze` ([docs/RELATION_SEARCH.md](../../docs/RELATION_SEARCH.md)). `reader.py`: `to_items` (the query as items, each the entities it may be, and kind words), then `to_groups`; `relations.py`: `RelationSearch`, the lists (`ResultList`: kind, filters, the list it follows, entities); `headings.py`: their wording, built when the API sends them |
| `search.py` | `SearchEngine`: a kind word → the relation search, otherwise the name search (scores, reasons, ranking); the API's entry point |
