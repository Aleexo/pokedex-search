# search/names

The name search: a partial or misspelt name → the closest Pokémon, moves, abilities and types. The rules are in
[docs/SEARCH.md](../../../docs/SEARCH.md).

| File | Role |
|---|---|
| `normalize.py` | `normalize` (accents, case, punctuation) |
| `resolver.py` | `EntityResolver`: the names closest to the query (`Candidate`: distance, exact, at start); `resolve_names` splits a query into `Piece`s (a word or a name of several words, with its candidates), keeping a caller's special words (the relation search's kind words); `distance` and `typos_allowed`: the typo rule, shared with the kind words |

## Matching from any word

People often remember a later word (`mime`, `wave`). Each name is indexed **from each of its words on**:
`high jump kick` → `high jump kick`, `jump kick`, `kick`.

| Query | Each word alone | Name + each word alone | From each word on (chosen) |
|---|---|---|---|
| `wave` | found | found | found |
| `thunder wa` | lost | found | found |
| `jump ki` | lost | lost | found |

## Why OSA

The measure must **count typos** (the rules and the reason shown are in typos) and **work on the start of a
name** (queries are partial). OSA (Levenshtein plus a swap of neighbours = 1) on the name cut to the query's
length does both. It is computed with `rapidfuzz` (`OSA.distance`, in C++): the same values as the
hand-written version it replaced on 20,000 random pairs, faster, and one function less to maintain.

| Alternative | Problem |
|---|---|
| Hamming | same length only: one missing letter shifts the rest (`pikchu` vs `pikach`: 3, OSA: 1) |
| Whole-name distance | penalises the missing end: `bulbi` is 3 from Vulpix, 5 from Bulbasaur |
| `difflib.get_close_matches` | whole strings: `bulbi` → nothing, `char` → Charizard, Healer, Harden; its ratio can't be explained |
| Embeddings | measure meaning, not spelling; no typo count; a large model for 447 names |
| Plain Levenshtein | a swap costs 2: `chramandr` (swap + missing letter) is 3, too far; OSA gives 2 |

The reordering rule (same letters, right first letter = 1) is kept on top of OSA for letters moved further
(`pichuka`).
