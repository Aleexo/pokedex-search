# Search

Find a Pokémon, move, ability or type from a partial or misspelt name, see why it matched, confirm it.
Code: `backend/search/names/`, `backend/search/search.py`. Routes: `/api/search`, `/api/pokemon`,
`/api/entity/{kind}/{name}`.

## Goal

"What was that Pokémon called?" A result is **relevant** when:
1. the intended name comes **first**, even from its start or with typos (`bulba`, `bulbi`, `pichuka`);
2. there is **little noise**: only the closest names;
3. each hit gives its **reason** ("Close to 'pikchu' (possible typo)") and opens a **details panel** to confirm it.

A query can also name several things (`pikachu thunderbolt`): each is found. Asking for what is linked to
them (`poison moves`) is the relation search: [RELATION_SEARCH.md](RELATION_SEARCH.md).

## Definitions

| Term | Meaning |
|---|---|
| **Name** | An entity's dataset name: 447 names (151 Pokémon, 164 moves, 114 abilities, 18 types) |
| **Normalise** | NFKD, no accents, lowercase, apostrophes removed, other punctuation and `-` → space (`Mr. Mime` = `mr mime`) |
| **Query** | The whole input, normalised, read as **one** name; if it is none, as the **names** it contains (`raichu and pikachu`) |
| **Distance** | OSA edit distance (`rapidfuzz`; insert, delete, replace, swap of neighbours = 1) to the **start** of a name, cut to the query's length ±1; 0 = the name starts with the query |
| **Later word** | The name from one of its later words on: `high jump kick` → `jump kick`, `kick` |

## Rules

| Rule | Why |
|---|---|
| Compare with the **start** of each name | `bulbi` is 1 typo from *bulba*; against whole names it would be closer to Vulpix (3) than Bulbasaur (5) |
| **Prefix** (distance 0) needs ≥ 2 letters | 1 letter matches up to 84 names; 2 letters at most 15 |
| **Typos**: 1 for 4–6 letters, 3 from 7 letters | more on short words would match unrelated names; from 7 letters a long name or a plural fits (`abilities` → ability, 3); measured: the 48 labelled cases unchanged |
| At **3 letters**, 1 typo only against names of ≤ 4 letters | `mow` → Mew, `dgi` → Dig; against every name `mwe` would match 13 |
| **Same letters reordered**, right first letter = 1 typo | `pichuka` → Pikachu (OSA alone: 4); the first letter stops `team` → Metapod |
| Keep **only the smallest distance** | a typo match never mixes with exact or prefix matches |
| Order: exact, start of name, later word | `mew` → Mew, then Mewtwo; `char` → Charmander… then Cute Charm |
| **Several names** only when the whole query is no name, read left to right | single names work as before |
| A name of several words is kept **whole** when written in full (typos from 6 letters: 1 at 6, 2 above) | `thunder wave pikachu` → Thunder Wave, Pikachu, not Thunder + Wave. Stricter than single words on purpose: these phrases are cut from a sentence, and at 3 typos `and fire` (in `blaze and fire blast`) would be Sand Force |
| ...unless it is misspelt and each of its words is a name | `pikachu fire blaze` → Fire, Blaze, not Fire Blast with 2 typos; `thunder wabe` stays Thunder Wave |
| Every other word of **3+ letters** gets its closest matches, as if searched alone; a kind word (`pokemon`, `moves`…) is never looked up as a name | `beam and pikachu` → the 5 beams and Pikachu; `bulba pikachu` → Bulbasaur, Pikachu; `and`, `or`, `vs` match nothing |

Each hit gets a score and a reason:

| Match | Score | Reason shown |
|---|---|---|
| Exact | 1.0 | Name matches |
| Start of name | 0.9 | Name starts with '…' |
| Later word | 0.85 | A word of the name starts with '…' |
| Typo | 0.9 or 0.85, −0.1 per typo | Close to '…' (possible typo) |

Ties: Pokémon → move → ability → type, then Pokédex number. No match: a note. Brute force over 447 names
takes well under a millisecond.

## API

`GET /api/search?q=bulbi&page=1`

```json
{"query": "bulbi", "notes": [], "page": 1, "pages": 1, "total": 1,
 "hits": [{"kind": "pokemon", "name": "bulbasaur", "label": "Bulbasaur", "score": 0.8,
           "reasons": ["Close to 'bulbi' (possible typo)"], "types": ["grass", "poison"], "pokemon": {"id": 1, "…": "…"}}]}
```

`/api/pokemon?page=2`: all Pokémon in Pokédex order, same shape, empty `query`. `/api/entity/{kind}/{name}`: the
details panel. 404 past the last page or for an unknown name; 422 for an invalid kind.

## UI

- Search box with examples; the query is in the URL (`?q=bulbi`).
- Empty box: all Pokémon in Pokédex order. Results come 20 per page (`?q=char&page=2`, `?page=2`); today no
  search has more than 15 matches (`po`).
- Each result: name, kind, type badges, reason, sprite. Keyboard: Tab or ↑/↓, Enter.
- Details panel: sprite, types, stats, evolution family, abilities, moves, coverage. Every name links.
- Hover cards (mouse or keyboard focus): a Pokémon's sprite, name and types; a move's type, class and power.

## Tests

- **48 labelled cases** (`backend/tests/cases/resolver.yaml`): traps (`hypno` vs Hypnosis, `growl` vs
  Growlithe), formatting (`Mr. Mime`), partial (`thunder wa`, `mime`), typos (`pikchu`, `chramandr`, `mow`),
  several equal matches (`psychic`: type and move), nothing (`qwzx`, `the`, `p`).
- Normalisation, the OSA distances the rules rely on, ranking, reasons, paging, API.
- Several names: `raichu and pikachu`, `pikachu thunderbolt`, `thunder wave pikachu`, `bulba pikachu`,
  `beam and pikachu`; words under 3 letters left aside (`raichu to pikachu`).

## Limitations

- Names only: no search by description ("moves that put the opponent to sleep"); no localised names.
- In a sentence, small words of 3+ letters find names too: `best attack against water` also lists Rest,
  Self-Destruct, Wing Attack… (measured: 26 of 80 common words match something). A sentence with a kind word
  goes to the relation search instead (`best move against water type`: no match).
- No typos under 3 letters; prefixes need 2.
- A common word close to a name matches it (`team` → Double Team).
