# Move coverage

In a Pokémon's details, the moves of other types that get past the types its own moves handle badly.
Code: `backend/coverage/`. Route: `/api/coverage/{name}`.

## Goal

"Which moves should it learn?" The answer is **useful** when the moves that get past the most walls come first,
super-effective ones before merely not resisted ones, and each line shows how the move does on every wall.

## Definitions

| Term | Meaning |
|---|---|
| **Walls** | The types resisting **all** of its own types (×0.5 or less, ×0 included), among the 18 types. Charizard (Fire / Flying): Rock. Geodude: none |
| **Candidate move** | A move it learns, with a power, of **another type** than its own (no STAB) |
| **×2, ×1** | How many walls the move hits ×2 (super-effective), and how many ×1 (not resisted) |
| **Estimated damage** | power × accuracy × the stat it uses (Attack if physical, Sp. Atk if special): the tie-break |
| **Type chart** | `data/type_chart.json`: the 18 types' multipliers, fetched once from PokeAPI and committed; the app never calls PokeAPI |

## Rules

| Rule | Why |
|---|---|
| Up to **5 moves** hitting at least one wall ×2 or ×1 | a move resisted by every wall gets past nothing |
| First the moves hitting walls **×2**, by how many | super-effective coverage matters most |
| Then the moves hitting walls **only ×1**, by how many | a move that isn't resisted still gets past; 28 Pokémon have nothing better |
| Ties by **estimated damage**, with the Pokémon's own stat | a physical move hits with its Attack, a special one with its Sp. Atk |

Snorlax (Normal; walls Ghost, Rock, Steel):

| Move | Class | Ghost | Rock | Steel | ×2 | ×1 |
|---|---|---|---|---|---|---|
| Earthquake | Physical (Atk 110) | ×1 | ×2 | ×2 | 2 | 1 |
| Submission | Physical (Atk 110) | ×0 | ×2 | ×2 | 2 | 0 |
| Solar Beam | Special (Sp. Atk 65) | ×1 | ×2 | ×0.5 | 1 | 1 |
| Fire Blast | Special (Sp. Atk 65) | ×1 | ×0.5 | ×2 | 1 | 1 |
| Surf | Special (Sp. Atk 65) | ×1 | ×2 | ×1 | 1 | 2 |

Pikachu (walls Dragon, Electric, Grass, Ground): Surf (×2 on 1), then Skull Bash, Double-Edge, Mega Kick, Body
Slam (×1 on all 4, by damage). Bulbasaur (walls Poison, Steel): no move hits them ×2, so its list is five ×1
moves (Double-Edge, Body Slam, Take Down, Cut, Tackle).

On the 151 Pokémon:

| Case | Pokémon | Shown |
|---|---|---|
| A list | 112 | the table |
| No wall | 22 (Gengar, Geodude…) | a note |
| No damaging move | 3 (Metapod, Kakuna, Ditto) | a note |
| Only moves of its own types | 9 | a note |
| Every other-type move resisted by all its walls | 5 (Butterfree, Exeggcute, Exeggutor, Scyther, Moltres) | a note |

## API

`GET /api/coverage/charizard`

```json
{"pokemon": "charizard", "walls": ["rock"], "notes": [],
 "moves": [{"kind": "move", "name": "earthquake", "label": "Earthquake", "type": "ground", "power": 100,
            "accuracy": 100, "pp": 10, "damage_class": "physical", "stat": 84, "damage": 8400.0,
            "multipliers": {"rock": 2}, "hits": 1, "neutral": 0}]}
```

`hits`: walls hit ×2; `neutral`: walls hit ×1. 404 for an unknown Pokémon.

## UI

- Under the Pokémon's moves: its walls as type badges, in a row of their own.
- One table line per move: type, Physical / Special with the stat used, power, accuracy, PP, a multiplier per wall
  (×2 green, below ×1 red; a bar on each side of these columns), then how many walls it hits ×2 and ×1.
- A note instead of the table when the list is empty.

## Tests

Values computed independently from the JSON: walls (Charizard, Pikachu, Geodude), lists with their ×2 and ×1
counts (Charizard, Pikachu, Snorlax, Bulbasaur), damage (Pikachu's Surf: 90 × 100 % × 50 = 4500), edge cases
(Geodude, Metapod, Butterfree), and every rule and the order checked on all 151 Pokémon.

## Limitations

- **Walls are offensive**, not the types that threaten the Pokémon.
- **Only the walls count**, not overall coverage: how a move does against the other types (those that resist only
  one of its types, or none) is ignored.
- The list is empty for 39 Pokémon: 22 have no wall, the others' Gen 1 learnsets have nothing past their walls.
- A ×1 move is only "not resisted": for 28 Pokémon (Bulbasaur…) the list is all ×1 moves, often Normal ones.
- Moves without a power are left out, though 12 of them do damage: fixed damage (Seismic Toss, Night Shade,
  Dragon Rage…), one-hit KOs (Guillotine, Fissure…), Low Kick, Counter, Bide.
- Moves are ranked one by one, not as a set of 4.
- A ×0 on another wall costs nothing (Submission ties Earthquake for Snorlax; the ×0 shows in red).
- Estimated damage ignores level, defender, STAB, abilities, items and drawbacks (Hyper Beam's recharge).
- Dark counts like any type although no Gen 1 Pokémon is Dark: it's a wall of the 7 Psychic Pokémon. Kept so
  the rule doesn't depend on the data.
- Mixed eras: Gen 1 moves with today's type chart and today's Physical / Special class per move. In Gen 1 the
  class came from the type, so the stat shown (Attack or Sp. Atk) is not always the one Gen 1 used.
