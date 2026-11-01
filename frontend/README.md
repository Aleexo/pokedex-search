# frontend

Vue 3 + TypeScript, one file per component, built by Vite. FastAPI serves the build (`dist/`).

**macOS / Linux**

```bash
npm install        # once
npm run build      # type check + build into dist/ (then start FastAPI, open http://localhost:8000)
npm run dev        # while editing: http://localhost:5173, live reload, /api forwarded to FastAPI on :8000
```

**Windows (PowerShell)**: `npm.cmd`, since PowerShell blocks `npm`'s script form by default.

```powershell
npm.cmd install    # once
npm.cmd run build  # type check + build into dist/ (then start FastAPI, open http://localhost:8000)
npm.cmd run dev    # while editing: http://localhost:5173, live reload, /api forwarded to FastAPI on :8000
```

| File | Role |
|---|---|
| `src/App.vue` | the page: title, tabs, the two views |
| `src/state.ts` | shared by all components: the open entity, `open()`, `close()`, `isOpen()`, the error |
| `src/api.ts` | the API's JSON shapes as TypeScript types, and `getJson` |
| `src/util.ts` | type colours, stat labels, keyboard and image helpers |
| `src/style.css` | styles shared by several components (each component has its own `<style scoped>`) |

`src/components/`, by the part of the page they draw:

| Folder | Components |
|---|---|
| `search/` | `SearchView` (box, results by pages, the state in the URL), `ResultList` (the rows; relation lists folded under their heading, each paged on its own) |
| `details/` | `DetailsPanel` (header, then one panel per kind): `PokemonPanel`, `MovePanel`, `AbilityPanel`, `TypePanel`; `CoverageTable` |
| `explore/` | `ExploreView` (choices and URL), `ExploreMenus` (sidebar), `TypeFilter`, `BarChart` (SVG), `ExploreTable` |
| `shared/` | `TypeBadge`, `EntityChips` (linked names, with a hover card for Pokémon and moves), `ToggleButtons` |

- **No relaying**: any component calls `open(kind, name)` from `state.ts`; props only carry the data to show.
- **Typed**: `api.ts` mirrors the backend's responses; `vue-tsc` checks every component, templates included.
- **State in the URL** (`?q=bulbi`, `?page=2`, `?lists=2,0` for the relation lists, `?view=explore&x=attack`), so
  views can be shared; switching tabs keeps each view's state (`KeepAlive`).
