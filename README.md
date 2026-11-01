# Pokédex Search

A Pokédex that runs locally, over 151 Pokémon, 164 moves, 114 abilities and 18 types, with three features for
now: **Search**, **Explore** and **Move coverage**.

## Run it

Needs Python 3.11+ with [uv](https://docs.astral.sh/uv/), and Node.js 20+. No API key.

From the repository's root folder. The server runs until Ctrl+C, so it comes last.

**macOS / Linux**

```bash
uv sync --directory backend --extra dev                    # once
npm --prefix frontend install                              # once
npm --prefix frontend run build                            # type-check and build the page (again after frontend edits)
uv run --directory backend pytest                          # tests, docstring examples, type check
uv run --directory backend uvicorn api.main:app --reload   # open http://localhost:8000
```

**Windows (PowerShell)**: `npm.cmd`, since PowerShell blocks `npm`'s script form by default.

```powershell
uv sync --directory backend --extra dev                    # once
npm.cmd --prefix frontend install                          # once
npm.cmd --prefix frontend run build                        # type-check and build the page (again after frontend edits)
uv run --directory backend pytest                          # tests, docstring examples, type check
uv run --directory backend uvicorn api.main:app --reload   # open http://localhost:8000
```

One process serves the API and the built page. Everything works offline except the sprites (remote URLs).
While editing the frontend: `npm --prefix frontend run dev` (Windows: `npm.cmd`), live reload on http://localhost:5173.

## The product

A Pokédex for trainers. Each feature answers one question and shows why its answer fits.

### Search: "what was that Pokémon called?"

A trainer remembers "bulba…" and wants to find the Pokémon and confirm it's the one. A result is **relevant** when:
1. the intended name comes **first**, even from its start only or with typos (`bulba`, `pikchu`, `mime`);
2. there is **little noise**: only the closest names;
3. the user sees **why** it matched ("Name starts with 'bulba'") and can **confirm** it in the details panel.

Only names are compared (Pokémon, moves, abilities, types), with an **edit distance to the start of each name**:
`bulbi` is 1 typo from *bulba(saur)*, where a whole-name distance would prefer Vulpix. Later words count too
(`mime` → Mr. Mime). A query naming several things (`raichu and pikachu`, `beam and pikachu`) finds what each
of its names finds. An empty box lists all Pokémon, page by page. Searching by meaning ("moves that put the
opponent to sleep") was left out to keep the search small, tested and explainable.
Details: [docs/SEARCH.md](docs/SEARCH.md).

With a **kind word** (`pokemon`, `moves`, `abilities`, `types`), the search asks for what is **linked** to the
names: `poison moves`, `fire pokemon ability blaze and fire blast` (→ Charmander, Charmeleon, Charizard),
`blaze pokemon moves`. Each list has a heading saying what it holds ("Pokémon of type Fire with Blaze and that
learn Fire Blast"), so a word read wrongly shows. The lists come folded, each paged on its own.
Details: [docs/RELATION_SEARCH.md](docs/RELATION_SEARCH.md).

### Explore: "which are the fastest, the strongest?"

Rank Pokémon or moves on one field (Speed, Attack… or power, accuracy…), one row each or one per type, highest
or lowest. The answer is **useful** when it fits on one screen (8 rows, as a bar chart or a table), types are
compared on averages, moves without a value aren't ranked as zero, and rows tied with the 8th are announced, not
hidden. A type filter narrows the rows; the state is in the URL, so a chart can be shared.
Details: [docs/EXPLORE.md](docs/EXPLORE.md).

### Move coverage: "which moves should it learn?"

In a Pokémon's details. Its **walls** are the types resisting all of its own types (Charizard: Rock); coverage
lists up to 5 moves of **other types** that get past them: first those hitting walls ×2, then those hitting walls
only ×1, each by how many walls, ties by estimated damage with its own Attack or Sp. Atk. Snorlax → Earthquake,
Submission, Solar Beam, Fire Blast, Surf. The type chart was fetched once from PokeAPI and committed.
Details: [docs/MOVE_COVERAGE.md](docs/MOVE_COVERAGE.md).

## Architecture

```
backend/
  domain/    typed records (dataclasses), in-memory Repository
  search/    names/: normalisation, edit distance, ranking; relations/: kind words, groups, links, headings
  explore/   ranking on one field, by type
  coverage/  type chart, coverage moves
  api/       FastAPI routes; also serves the frontend
  tests/
frontend/    Vue 3 + TypeScript components, built by Vite
data/        pokedex.json (unchanged), type_chart.json
scripts/     fetch_type_chart.py (run once), relation_cases.py (writes the relation search's expected cases)
docs/        one design doc per feature
```

- **No database**: 478 KB, read-only, loaded once.
- **Features don't depend on FastAPI**: `SearchEngine.from_data().search("bulbi")` works in a shell.
- **Typed**: records are dataclasses and kinds / fields are enums, checked by mypy as part of the tests.
- **Charts are plain SVG**: no chart library.
- **Frontend split into components** (`.vue` files), with the API's responses as TypeScript types.

## Validation

`uv run pytest`: **277 checks**, all passing.
- **48 labelled search cases** ([resolver.yaml](backend/tests/cases/resolver.yaml)): exact names and traps (`mew` vs
  Mewtwo), partial, typos, several equal matches, must-match-nothing (`qwzx`). Each bug found by hand became a case.
- **49 labelled relation cases** ([relations.yaml](backend/tests/cases/relations.yaml)): headings, counts and
  items, worked out from the data before the code was written; now computed by
  [scripts/relation_cases.py](scripts/relation_cases.py) independently of the code, and a test checks the file
  matches the script.
- **Unit and API tests**; expected values recomputed from the JSON, independently of the code.
- **106 docstring examples** run as tests, so docs can't drift from the code.
- **mypy** runs inside the suite; the frontend is type-checked on every build (`vue-tsc`).
- UI checked by hand and with headless-browser click tests and screenshot comparisons (not part of the suite).

## Limitations

- Names only: no search by description ("moves that put the opponent to sleep"), no localised names.
- In a sentence, small words find names too (`with` → Withdraw), and words one typo from a kind word act as one
  (`more` → moves): the search expects names.
- Relation search: no "and" between items of the same kind (no Pokémon both Fire and Flying); chains through
  common moves return almost everything; a chain's heading gets long past two steps.
- A 3-letter typo only finds names of up to 4 letters (`mow` → Mew).
- Type averages in Explore hide spread.
- Data mixes eras: Gen 1 moves, modern abilities and types.
- No automated frontend tests: the type check, and the browser checks above.

## Next steps

- **All generations**: the full data fetched once from PokeAPI and committed, like the type chart; a generation
  filter in Search and Explore; the search rules re-measured on about 2,500 names.
- **Team builder**: pick 3 to 6 Pokémon, see the types that threaten several of them and the types nobody hits
  ×2, and get Pokémon that fill those gaps.
- **Weather**: who sets it (Rain Dance, Drizzle…), which moves it boosts, which Pokémon benefit (Swift Swim…).
- **Evolution methods** in the details panel: level, stone, trade, friendship.
- **Egg groups**: which Pokémon can breed together and pass a move on.
- **Search by meaning**: intent tags (inflicts sleep, benefits from rain) linking moves, abilities and Pokémon.
- **AI assistant**: a chat that helps trainers work out what they need ("a team for the Elite Four", "something
  to beat Water types"), asks follow-up questions, then answers with the app's own tools (search, Explore, coverage,
  team builder) and shows why. Optional, since it needs an LLM and an API key; the rest stays offline.
- **Several languages**: the names translated (French, German, Japanese…), so the Pokédex can be searched and
  read in each.

## AI-use disclosure

Built with **Claude (Anthropic) through Claude Code** as a pair programmer.

**How we worked.** I set the direction and made the product and design decisions; the AI wrote most of the
code, tests and docs, proposed options with their trade-offs, and ran the checks. I reviewed the code folder by
folder and asked for changes where it was more complex than needed. Before accepting a rule, I had it
measured on the data; a failing check was investigated, never adjusted to pass.

**Main decisions**

*Product*
- **Features**: I chose three, each answering one trainer's question: recover a half-remembered name, rank on
  one field, find the moves that get past the types resisting a Pokémon.
- **Scope**: searching by meaning (intent tags, aliases, "did you mean") was tried, then removed at my request
  to keep the search small and testable.

*Search*
- **Measure**: I chose one edit distance to the **start** of each name; the AI compared it with Hamming,
  `difflib` and embeddings, and OSA (via `rapidfuzz`) replaced plain Levenshtein after discussion.
- **Limits**: the prefix length and typo limits were measured on the data before being fixed.
- **Code structure**: asked for during review: typed records and enums checked by mypy instead of dict keys and
  strings; entities identified by their kind and number, names only at the edges (URLs, API, test files); a
  runnable example on every function, called with its real inputs; every wrong result found by hand turned into
  a labelled case.

*Relation search*
- **Origin**: I wanted results based on the links between entities: `poison moves` → the Poison moves,
  `fire pokemon ability blaze and fire blast` → the Pokémon matching all three.
- **Design**: agreed in discussion on example queries, before coding. I sketched entities and kind words as a
  graph and settled the rules: no inference without a kind word; a query read as a kind with filters, chains as
  nested groups (`((psychic pokemon) + fire) moves`); each kind word takes the items before it; "or" within a
  kind, "and" across kinds. The AI listed the ambiguous cases for me to decide (for these, its suggestion of
  showing both readings was kept) and computed the expected results from the data.
- **Code structure**: changes asked for during review: `names/` and `relations/` kept apart; the query read as
  entities and kind words first, then grouped, reusing the name search's split; each word resolved before
  grouping; the headings' wording built only when the lists are sent; entities identified by kind and number,
  with a parent class for the four records and links read from them; one typo rule for names and kind words,
  extended for plurals instead of a special case; the expected results computed by a separate script,
  independently of the code, so they can be recomputed.
- **Clarifications**: I asked why some steps worked as they did (a distance computed inside each group, a list
  feeding the next group), for an unreadable one-line rule to be rewritten, and for docstrings that state each
  method's goal with examples on real inputs. Several led to simpler code.
- **Display**: each list folded and paged separately, the state in the URL.

*Explore*
- **Specification**: I set it: one field, 8 rows that fit on one screen, highest or lowest, by type or not. A
  scatter plot and grouping by ability were built, then removed after review.
- **Code structure**: asked for during review: the fields and orders as enums checked by mypy, and the subject
  (Pokémon or moves) given by the field itself (Power ranks moves) rather than stored apart; no dependency on
  the web layer.

*Coverage*
- **Rules**: reworked several times at my request, down to one list: moves of other types that get past the
  types resisting the Pokémon, ×2 first, then ×1.
- **Code structure**: asked for during review: the type chart fetched once by a script and committed, so the app
  never calls PokeAPI; no special case for today's data (Dark, Explosion), so the rules hold if the data changes.

*Frontend and docs*
- **Frontend**: Vue + TypeScript components, one file per component, grouped by folder, chosen for readability.
- **Docs**: one design doc per feature and one README per module, rewritten at my request to be short.
