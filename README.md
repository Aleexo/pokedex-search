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
  search/    normalisation, edit distance, ranking
  explore/   ranking on one field, by type
  coverage/  type chart, coverage moves
  api/       FastAPI routes; also serves the frontend
  tests/
frontend/    Vue 3 + TypeScript components, built by Vite
data/        pokedex.json (unchanged), type_chart.json
docs/        one design doc per feature
```

- **No database**: 478 KB, read-only, loaded once.
- **Features don't depend on FastAPI**: `SearchEngine.from_data().search("bulbi")` works in a shell.
- **Typed**: records are dataclasses and kinds / fields are enums, checked by mypy as part of the tests.
- **Charts are plain SVG**: no chart library.
- **Frontend split into components** (`.vue` files), with the API's responses as TypeScript types.

## Validation

`uv run pytest`: **199 checks**, all passing.
- **48 labelled search cases** ([resolver.yaml](backend/tests/cases/resolver.yaml)): exact names and traps (`mew` vs
  Mewtwo), partial, typos, several equal matches, must-match-nothing (`qwzx`). Each bug found by hand became a case.
- **Unit and API tests**; expected values recomputed from the JSON, independently of the code.
- **82 docstring examples** run as tests, so docs can't drift from the code.
- **mypy** runs inside the suite; the frontend is type-checked on every build (`vue-tsc`).
- UI checked by hand and with headless-browser click tests and screenshot comparisons (not part of the suite).

## Limitations

- Names only: no search by description ("moves that put the opponent to sleep"), no localised names.
- In a sentence, small words find names too (`move` → Mirror Move): the search expects names.
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

**How we worked.** I set the direction and made every product and design decision; the AI wrote most of the
code, tests and docs from those decisions, proposed options with their trade-offs, and ran the checks. I
reviewed the code folder by folder and asked for changes until each part was as simple as I wanted. Before
accepting a rule, I asked for it to be measured on the data; a failing check was investigated, never adjusted
to pass.

**What I decided or asked for:**

*Product and scope*
- The product: a Pokédex with three features, each answering one trainer's question (above).
- The search situation (a partially remembered name) and what makes a result relevant; searching by meaning
  left out to keep the scope small.
- Explore's specification: one field, 8 rows, highest or lowest, bar chart or table, type colours, a type
  filter, the state in the URL.
- Move coverage as the last feature, and its rules: walls = types resisting **all** its types, moves of other
  types only, ranked ×2 first then ×1, damage with the Pokémon's own Attack or Sp. Atk.

*Search*
- One edit distance to the **start of each name**, replacing exact / prefix / fuzzy tiers, trigram similarity
  and a candidate cap.
- The distance compared with Hamming, `difflib` and embeddings in the docs, then OSA instead of Levenshtein.
- The minimum prefix measured and set to 2 letters; typos at 3 letters, only against short names (`mow` → Mew).
- Names matched from any of their words (`mime` → Mr. Mime, `jump ki` → High Jump Kick).
- Removed: aliases, stop words, intent tags, "did you mean", suggestions while typing.

*Explore and coverage*
- Moves ranked on their own fields; type filter **or** grouping by type, not both; ties at the 8th row shown.
- A subject given by the field (Power ranks moves) instead of four group values.
- Removed after review: a scatter plot of two fields, grouping by ability, ability and move filters, Priority.
- Coverage reworked several times (counters, "weaknesses", gaps) down to one list; the type chart fetched once
  and committed; special cases removed so the rules don't depend on today's data (Dark, Explosion).

*Code*
- Enums instead of strings, checked by mypy inside the tests; typed records instead of dict keys.
- A docstring with a runnable example on every backend function; unused code removed folder by folder.
- Sorting only where ranking is the feature; the repository independent of where the data comes from.

*Frontend*
- Vite + Vue components + TypeScript, for readability: one file per component, grouped by folder, shared state
  instead of events passed through every layer.
- Results paged; hover cards for Pokémon (sprite, types) and moves (type, class, power); wall badges on their
  own row; keyboard navigation; clickable type badges.

*Docs*
- One README per module and one design doc per feature, then rewritten to be short and easy to read.
