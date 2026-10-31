# Explore

Rank Pokémon or moves on one field, as a bar chart or a table; each row opens its details.
Code: `backend/explore/`. Routes: `/api/explore`, `/api/explore/fields`.

## Goal

"Which Pokémon are the fastest?", "which type hits hardest?", "which moves are the most powerful?" The answer is
**useful** when it fits on one screen, compares like with like, and hides nothing.

## Definitions

| Term | Meaning |
|---|---|
| **Subject** | Pokémon or moves; the fields offered follow it. Stored as the field itself (Power ranks moves), so the two can't disagree |
| **Field** | Pokémon: HP, Attack, Defense, Sp. Atk, Sp. Def, Speed, height (m), weight (kg)<br>Moves: power, accuracy, PP, effect chance |
| **Rows** | One per Pokémon or move, or one per type (`by_type`: the field averaged) |
| **Order** | Highest or lowest |
| **Type filter** | Pokémon with any of the types, or moves of those types |

## Rules

| Rule | Why |
|---|---|
| **8 rows** max | enough to compare, short enough to read at a glance |
| Type rows **average** the field; a two-type Pokémon counts in both | comparable across type sizes; the table shows counts |
| Moves ranked on **their own** fields | "most powerful moves" means the moves, not their learners |
| Moves **without a value** left out | 67 have no power, 32 status moves no accuracy; ranking them as 0 would fill the bottom |
| A damaging move **without accuracy** counts as 100 % | it never misses (Swift), as in move coverage |
| Filter by type **or** group by type | together, the filter only hid bars or skewed averages |
| **Ties** at the 8th row counted | "+ 3 more tied at 120, not shown" instead of hiding them |

Ties are broken by name. 151 or 164 records per request: well under a millisecond.

## API

`GET /api/explore?x=power[&by_type=true]&order=top[&types=fire]`

```json
{"x": "power", "subject": "move", "by_type": false, "order": "top", "matched": 164, "total": 164,
 "noun": "moves", "tied_beyond": 3,
 "rows": [{"kind": "move", "name": "explosion", "label": "Explosion", "x": 250, "count": 18, "types": ["normal"]}]}
```

`count`: Pokémon (or moves) averaged; for a move, the Pokémon learning it. `/api/explore/fields`: the menus.
422 for an unknown field or type, or a type filter with `by_type`.

## UI

- Pokémon / Moves switch; sidebar: Group by, Rank by, Highest / Lowest.
- Type filter above the chart, with "44 of 151 Pokémon"; greyed out when grouping by type.
- Bar chart (type colours, two halves for two types) or table, the same 8 rows. Plain SVG.
- The state is in the URL (`?view=explore&x=attack&by_type=true`).

## Tests

Expected values recomputed from the JSON: top and bottom (Electrode 150, Slowpoke 15), Dragon's average
Speed 66.7, moves by power (Explosion 250), Fire moves' average power 70.0, Fire + Water = 44 Pokémon, ties
at the 8th row, every 422.

## Limitations

- One field at a time.
- Only the top or the bottom of a ranking: never the middle, nor the rows around a given value (the Pokémon
  closest to Pikachu's Speed, say).
- The type filter is "any of" only: no Pokémon that are both Fire **and** Flying.
- Averages hide spread; small types can lead (Ghost, 3 Pokémon, is 2nd in Speed).
- A type's average counts two-type Pokémon in both types and mixes every evolution stage: first stages pull it
  down, a Mewtwo pulls Psychic up.
- Moves are Gen 1: no Fairy or Steel moves.
