# Relation search

Ask for the Pokémon, moves, abilities or types linked to what you name: `poison moves`, `fire pokemon ability
blaze and fire blast`. Builds on the name search ([SEARCH.md](SEARCH.md)), which still finds each name.
Code: `backend/search/relations/` (`reader.py`: `to_items`, the query as items and kind words, then
`to_groups`; `relations.py`: the lists, each with its kind, filters and the list it follows; `headings.py`:
their wording, built when they are sent), and `Repository.linked` (the links, built once). Route: `/api/search`.

## Goal

"Which moves are Poison?", "which Fire Pokémon have Blaze and learn Fire Blast?". A result is **useful** when:
1. it holds exactly the entities linked to **everything** named, of the **kind** asked for;
2. a heading says what the list is ("Pokémon of type Fire with Blaze and that learn Fire Blast (3)"), so a
   word read wrongly shows;
3. a query without a kind word behaves exactly as before.

## Definitions

| Term | Meaning |
|---|---|
| **Kind word** | One word per kind: `pokemon`, `move`, `ability`, `type`, matched like a name (its start, typos: up to 3 from 7 letters, so plurals fit: `abilities` is 3 from `ability`): `poke`, `mov`, `typ`, `moves`, `pokmon`, `abilites`. An exact name wins (`agility` is the move); `Pokémon` = `pokemon` |
| **Item** | A name found in the query by the name search: a Pokémon, move, ability or type |
| **Link** | Pokémon ↔ type (is), Pokémon ↔ ability (has), Pokémon ↔ move (learns), move ↔ type (is). Nothing else: no ability ↔ move, no Pokémon ↔ Pokémon |
| **Label** | A kind word next to an item that is only of that kind (`ability blaze`, `fire type`, `thunderbolt move`): it names the item, it asks for nothing |
| **Group** | A kind word and the items it takes; its result is the entities of that kind linked to them |
| **Chain** | Several groups: each group's result filters the next (`blaze pokemon moves`: the moves of the Pokémon with Blaze) |

## Rules

**Reading the query**

| Rule | Why |
|---|---|
| Names are found as today: names of several words whole first (`fire blast`, `mirror move`), then each word of 3+ letters; words matching nothing are dropped (`and`) | the name search is unchanged and tested |
| A kind word is a **label** when the item next to it (before or after) is only of its kind, and no item before it can be filtered by it | `fire pokemon ability blaze` asks for Pokémon, not abilities; `pikachu moves thunder pokemon` keeps `moves` (Pikachu has moves) |
| **No kind word left**: the name search answers, as today | `pikachu thunderbolt` → Pikachu, Thunderbolt; no guessing of what is asked |
| Each kind word takes the items **before** it; the **last** one also takes those after | `moves pikachu` = `pikachu moves` |
| An item **between** two kind words goes to the one it can filter; if both, to the **next** one | `electric pokemon static moves`: Static (an ability) can only filter the Pokémon; `blaze pokemon fire moves`: Fire can filter both, so the moves |
| An item after the last kind word, of a kind its group already has, leaves the query without a reading: **no results** | `grass move fire`: Grass already filters the moves |
| An item that can filter neither kind: **no results** | `charizard abilities blaze`: an ability doesn't filter abilities |
| A kind word with no item: **all** of that kind | `pokemon` → 151, `moves` → 164 |

**Choosing a word's item**: each word (or name of several words) is mapped to its entities first, before the
groups are formed; only the last rule needs its group.

| Rule | Why |
|---|---|
| An **exact** name wins | `rock pokemon` → the Rock type, not Rock Head or Rock Slide |
| Otherwise the one **closest to the full name** (OSA on the whole name) | `posion` is 1 typo from *poison*, far from *poison point*; `char` → Charizard |
| In its group, keep those that can link to the group's kind | `snorlax moves psychic`: the type, as the move Psychic can't filter moves |
| Still tied: **one list per item** | `psychic pokemon` → Pokémon that learn Psychic (34), Pokémon of type Psychic (14) |

**Combining**

| Rule | Why |
|---|---|
| Items of **different kinds** in a group must **all** hold | `fire pokemon ability blaze and fire blast` → Charmander, Charmeleon, Charizard |
| Items of the **same kind**: **one list each** (or, never and) | `blaze overgrow pokemon` → the Blaze Pokémon, then the Overgrow Pokémon; `pikachu raichu moves` → each one's moves |
| In a chain, an entity passes if it links to **any** of the previous group's result | `ghost pokemon moves`: moves learned by at least one Ghost Pokémon |
| Results are returned whatever their size | `pikachu moves pokemon` → 145 of 151 |
| Empty lists are left out; if all are, the usual "No match" note | |

**Order**: lists in the order of the query's words; a word's tied entities in the order of the kind names
(ability, move, Pokémon, type: `psychic` gives the move's list, then the type's). Inside a list: by number (Pokédex number, move and ability number, PokeAPI's type number).

**Headings**: the kind, then one phrase per filter (type first, then ability, move, Pokémon, then the chain). A
type reads like an adjective, so the next phrase follows it directly ("Pokémon of type Fire with Blaze"); the other
phrases are joined with commas and "and":

| Result | Filter | Phrase | Example |
|---|---|---|---|
| Pokémon | type | of type X | Pokémon of type Fire (12) |
| Pokémon | ability | with X | Pokémon with Static (6) |
| Pokémon | move | that learn X | Pokémon that learn Thunderbolt (50) |
| Moves | type | of type X | Moves of type Poison (8) |
| Moves | Pokémon | learned by X | Moves of type Electric learned by Pikachu (4) |
| Abilities, types | any | of X | Types of Pokémon with Overgrow (2) |
| any | a chain | the previous heading, inside | Moves learned by Pokémon with Blaze (35) |

## API

`GET /api/search?q=poison+moves&page=1`: the same paged shape, plus `groups` (each list's heading and count) and,
on each hit, `group` (its list's index). A heading is strings and entities; an entity carries what its hover card
shows. All the hits come on one page (the lists are folded and page their rows themselves), in order. A name
search has `groups: []`, no `group`, and 20 hits per page.

```json
{"query": "poison moves", "notes": [], "page": 1, "pages": 1, "total": 8,
 "groups": [{"heading": ["Moves of type ", {"kind": "type", "name": "poison", "label": "Poison"}], "total": 8}],
 "hits": [{"kind": "move", "name": "poison-sting", "label": "Poison Sting", "group": 0, "score": null, "reasons": [], "…": "…"}]}
```

## UI

- Each list is **folded**, like the moves in the details panel: an arrow, its heading and its count; a click
  unfolds its rows. In the heading, a type is a badge and other entities are chips (hover card, click to open the
  entity, without unfolding the list).
- Inside a list, **20 rows per page** with the list's own ‹ Previous / Next ›; each list pages on its own. A new
  search folds every list and goes back to page 1.
- Which lists are open, and on which page, is in the URL: `?q=psychic+pokemon&lists=2,0` (one number per list: 0
  folded, n open on page n), so a shared link opens as it was.
- Examples under the box: `poison moves`, `fire pokemon ability blaze`.
- Everything else as in the name search: keyboard navigation, details panel, `?q=` in the URL.

## Tests

- **49 labelled cases** (`backend/tests/cases/relations.yaml`): one filter, typos and ties, several kinds, the
  same kind, labels, chains, a kind word alone, no results, no kind word (unchanged). Each gives the lists'
  headings, counts and items, written by `scripts/relation_cases.py`, which computes them from the data on its
  own (the links read from the JSON, the rules and wording written again); a test checks the file is what the
  script writes. The code gave the same results on its first run.
- Reading (labels, groups, items between kind words), links, headings: docstring examples; hits and their lists,
  the "No match" note, the API's `groups` and `group`.

## Limitations

- No **and** between items of the same kind: no "Pokémon both Fire and Flying".
- No guessing: without a kind word, no relation (`fire blaze fire blast` lists the three names).
- Every match is kept, so a common word can add a filter: `fire pokemon with blaze` finds nothing (`with` →
  Withdraw).
- Kind words are matched like names, so a word one typo away is one: `more`, `mode`, `love`, `movie` → move;
  `hype`, `tape`, `typo` → type; `pole`, `poker` → pokemon (`pikachu more` lists Pikachu's moves). No synonyms
  (`mon`, `attack`, `skill`) or abbreviations (`pkmn`); a swap in a short plural isn't caught (`mvoes`).
- An item between two kind words that can filter both always goes to the next one: `blaze pokemon fire moves`
  can't mean the moves of the Fire Pokémon with Blaze.
- Chains through common moves return almost everything (`pikachu moves pokemon`).
- A chain's heading gets long past two steps: "Pokémon of type Flying that learn moves of type Water learned by
  Pokémon with abilities of Blastoise".
- Only the links in the data: no evolutions, no move class or power as filters (`special moves`).
