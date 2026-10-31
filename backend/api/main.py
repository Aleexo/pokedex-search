"""HTTP layer. Thin on purpose: all search logic lives in `search`, this only shapes JSON.
It also serves the built frontend (frontend/dist, from `npm run build`), so one process runs the whole app.

Run: uv run uvicorn api.main:app --reload   (from backend/), then open http://localhost:8000
"""

import logging
import time
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from coverage import CoverageAdvisor, CoverageMove, TypeChart
from domain.repository import EntityRef, Kind, Repository
from explore import Explorer, Number, Order, Subject, tied_beyond
from explore.explorer import MAX_ROWS
from search import SearchEngine
from search.search import display_name

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("pokedex.search")

engine = SearchEngine.from_data()
repo: Repository = engine.repo
explorer = Explorer(repo)
advisor = CoverageAdvisor(repo, TypeChart.from_data())  # local type chart: no PokeAPI call at runtime
app = FastAPI(title="Pokédex Search")


def pokemon_summary(name: str) -> dict:
    """Pokémon fields for the result list and details panel, in display units (m, kg).

    >>> pokemon_summary("bulbasaur")["weight_kg"]
    6.9
    """
    p = repo.pokemon[name]
    return {
        "id": p.id,
        "types": p.types,
        "stats": asdict(p.stats),
        "height_m": p.height_m,
        "weight_kg": p.weight_kg,
        "sprite": p.sprite,
    }


def row_json(ref: EntityRef) -> dict:
    """One row of the result list: label, types for the badges and, for a Pokémon, its summary.

    >>> row = row_json(EntityRef(Kind.POKEMON, "pikachu"))
    >>> row["label"], row["types"], row["pokemon"]["id"]
    ('Pikachu', ['electric'], 25)
    """
    row = {**ref_json(ref), "types": _entity_types(ref)}
    if ref.kind is Kind.POKEMON:
        row["pokemon"] = pokemon_summary(ref.name)
    return row


def ref_json(ref: EntityRef) -> dict:
    """JSON form of an entity reference, with a display label.

    >>> ref_json(EntityRef(Kind.MOVE, "thunder-wave"))["label"]
    'Thunder Wave'
    """
    return {"kind": ref.kind, "name": ref.name, "label": display_name(ref.name)}


@app.get("/api/search")
def search(q: str = Query(..., min_length=1, max_length=200), page: int = Query(1, ge=1)) -> dict:
    """Search by name: one page of ranked hits with reasons, and notes. Logs one line per query.

    404 past the last page.

    Example: GET /api/search?q=char
    -> {"query": "char", "notes": [], "page": 1, "pages": 1, "total": 4,
        "hits": [{"kind": "pokemon", "name": "charmander", "score": 0.9, ...}, ...]}
    """
    started = time.perf_counter()
    response = engine.search(q)
    hits = [{**row_json(hit.ref), "score": hit.score, "reasons": hit.reasons} for hit in response.hits]

    # One structured line per query: what matched and how long it took.
    log.info(
        "query=%r hits=%d top=%s ms=%.1f",
        q, len(hits), [f"{h['kind']}:{h['name']}" for h in hits[:3]], (time.perf_counter() - started) * 1000,
    )
    return {"query": response.query, "notes": response.notes, **one_page(hits, page)}


@app.get("/api/pokemon")
def pokemon_page(page: int = Query(1, ge=1)) -> dict:
    """All Pokémon in Pokédex order, one page of result rows (shown when the search box is empty).

    404 past the last page.

    Example: GET /api/pokemon?page=8
    -> {"query": "", "notes": [], "page": 8, "pages": 8, "total": 151,
        "hits": [{"kind": "pokemon", "name": "kabutops", "types": ["rock", "water"], "reasons": [], ...}, ...]}

    >>> [h["name"] for h in pokemon_page(8)["hits"]][-2:]
    ['mewtwo', 'mew']
    """
    rows = [{**row_json(EntityRef(Kind.POKEMON, n)), "reasons": []} for n in repo.pokemon]  # dataset = Pokédex order
    return {"query": "", "notes": [], **one_page(rows, page)}


PAGE_SIZE = 20


def one_page(rows: list[dict], page: int) -> dict:
    """Page `page` of the rows, PAGE_SIZE per page, with the page count and total. No rows is one empty page;
    past the last page: 404.

    >>> p = one_page(list(range(45)), 3)
    >>> p["hits"], p["pages"], p["total"]
    ([40, 41, 42, 43, 44], 3, 45)
    """
    pages = max(1, -(-len(rows) // PAGE_SIZE))  # ceiling division
    if page > pages:
        raise HTTPException(404, f"No page {page}: there are {pages}")
    return {"page": page, "pages": pages, "total": len(rows), "hits": rows[(page - 1) * PAGE_SIZE:page * PAGE_SIZE]}


@app.get("/api/entity/{kind}/{name}")
def entity(kind: Kind, name: str) -> dict:
    """Details of one entity for the details panel. 422 for an invalid kind, 404 for an unknown name.

    Example: GET /api/entity/pokemon/bulbasaur
    -> {"name": "bulbasaur", "height_m": 0.7, "weight_kg": 6.9,
        "evolution_family": [{"name": "bulbasaur", ...}, {"name": "ivysaur", ...}, ...], ...}
    """
    # FastAPI validates `kind` against the enum (422 if invalid); unknown names are a 404.
    ref = EntityRef(kind, name)
    if not repo.exists(ref):
        raise HTTPException(404, f"Unknown {kind} {name!r}")
    base = ref_json(ref)

    if kind is Kind.POKEMON:
        p = repo.pokemon[name]
        return {
            **base, **pokemon_summary(name),
            "genus": p.genus,
            "description": p.description,
            "abilities": [{**ref_json(EntityRef(Kind.ABILITY, a)), "short_effect": repo.abilities[a].short_effect}
                          for a in p.abilities],
            "moves": [move_ref_json(m) for m in p.moves],
            "evolution_family": [pokemon_ref_json(n) for n in repo.evolution_family(name)],
        }
    if kind is Kind.MOVE:
        m = repo.moves[name]
        return {**base, "type": m.type, "power": m.power, "accuracy": m.accuracy, "pp": m.pp,
                "damage_class": m.damage_class, "short_effect": m.short_effect, "pokemon": _pokemon_refs(ref)}
    if kind is Kind.ABILITY:
        return {**base, "short_effect": repo.abilities[name].short_effect, "pokemon": _pokemon_refs(ref)}
    return {**base, "pokemon": _pokemon_refs(ref),
            "moves": [move_ref_json(m) for m in repo.moves_by_type.get(name, [])]}


def _pokemon_refs(ref: EntityRef) -> list[dict]:
    """Pokémon linked to an entity, in dataset order, each with its types and sprite.

    >>> [p["name"] for p in _pokemon_refs(EntityRef(Kind.MOVE, "spore"))]
    ['paras', 'parasect']
    """
    return [pokemon_ref_json(n) for n in repo.pokemon_with(ref)]


def pokemon_ref_json(name: str) -> dict:
    """A Pokémon's name with its types and sprite: enough for the card shown when the mouse is over its name.

    >>> p = pokemon_ref_json("ivysaur")
    >>> p["label"], p["types"], p["sprite"].endswith("/2.png")
    ('Ivysaur', ['grass', 'poison'], True)
    """
    p = repo.pokemon[name]
    return {**ref_json(EntityRef(Kind.POKEMON, name)), "types": p.types, "sprite": p.sprite}


def move_ref_json(name: str) -> dict:
    """A move's name with its type, class and power: enough for the card shown when the mouse is over its name.

    >>> m, growl = move_ref_json("surf"), move_ref_json("growl")
    >>> m["label"], m["type"], m["damage_class"].value, m["power"], growl["damage_class"].value, growl["power"]
    ('Surf', 'water', 'special', 90, 'status', None)
    """
    m = repo.moves[name]
    return {**ref_json(EntityRef(Kind.MOVE, name)), "type": m.type, "damage_class": m.damage_class, "power": m.power}


@app.get("/api/explore/fields")
def explore_fields() -> dict:
    """The fields the Explore menus offer, with their labels.

    Example: GET /api/explore/fields
    -> {"numbers": [{"name": "hp", "label": "HP", "subject": "pokemon"}, ...],
        "max_rows": 8, "filters": {"types": [{"kind": "type", "name": "bug", "label": "Bug"}, ...]}}
    """
    return {
        "numbers": [{"name": n.value, "label": n.label, "subject": n.subject} for n in Number],
        "max_rows": MAX_ROWS,
        # Only types some Pokémon has (no Gen 1 Pokémon is Dark), in dataset order.
        "filters": {"types": [ref_json(EntityRef(Kind.TYPE, t)) for t in repo.pokemon_by_type]},
    }


@app.get("/api/explore")
def explore(x: Number, by_type: bool = False, order: Order = Order.TOP, types: list[str] = Query([])) -> dict:
    """The 8 rows with the highest or lowest value of `x`, over the filtered Pokémon or moves.

    The field decides the subject: a move field ranks moves, any other field Pokémon. `by_type`: one row per
    type instead of one per Pokémon or move. 422 for an unknown field or type, or a type filter with `by_type`.
    `matched` / `total` count the Pokémon (or moves) passing the type filter. `tied_beyond`: rows not shown
    that tie with the last one shown.

    Example: GET /api/explore?x=speed&types=fire&types=water
    -> {"x": "speed", "subject": "pokemon", "by_type": false, "order": "top", "matched": 44, "total": 151,
        "noun": "Pokémon", "tied_beyond": 0,
        "rows": [{"kind": "pokemon", "name": "starmie", "label": "Starmie", "x": 115, "count": 1,
                  "types": ["water", "psychic"]}, ...]}
    """
    for name in types:
        if not repo.exists(EntityRef(Kind.TYPE, name)):
            raise HTTPException(422, f"Unknown type: {name}")
    chosen = frozenset(types)  # the type filter
    try:
        ranked = explorer.ranked(x, by_type, order, chosen)
    except ValueError as e:  # a type filter while grouping by type
        raise HTTPException(422, str(e))
    rows = ranked[:MAX_ROWS]
    moves = x.subject is Subject.MOVE
    return {
        "tied_beyond": tied_beyond(ranked),
        "x": x, "subject": x.subject, "by_type": by_type, "order": order,
        "matched": len(explorer.moves(chosen) if moves else explorer.pokemon(chosen)),
        "total": len(repo.moves) if moves else len(repo.pokemon), "noun": x.subject.noun,
        "rows": [{**ref_json(r.ref), "x": r.x, "count": r.count, "types": _entity_types(r.ref)} for r in rows],
    }


def _entity_types(ref: EntityRef) -> list[str]:
    """Types of an entity, for badges and Explore colours: a Pokémon's types, the type itself, a move's type; none for an ability.

    >>> _entity_types(EntityRef(Kind.POKEMON, "charizard")), _entity_types(EntityRef(Kind.MOVE, "surf"))
    (['fire', 'flying'], ['water'])
    """
    if ref.kind is Kind.POKEMON:
        return repo.pokemon[ref.name].types
    if ref.kind is Kind.TYPE:
        return [ref.name]
    if ref.kind is Kind.MOVE:
        return [repo.moves[ref.name].type]
    return []


@app.get("/api/coverage/{name}")
def coverage(name: str) -> dict:
    """A Pokémon's walls and its moves of other types that get past them (docs/MOVE_COVERAGE.md).

    404 for an unknown Pokémon.

    Example: GET /api/coverage/charizard
    -> {"pokemon": "charizard", "walls": ["rock"], "notes": [],
        "moves": [{"kind": "move", "name": "earthquake", "label": "Earthquake", "type": "ground", "power": 100,
                   "accuracy": 100, "pp": 10, "damage_class": "physical", "stat": 84, "damage": 8400.0,
                   "multipliers": {"rock": 2}, "hits": 1, "neutral": 0}, ...]}
    """
    if name not in repo.pokemon:
        raise HTTPException(404, f"Unknown Pokémon: {name}")
    report = advisor.suggest(name)
    return {"pokemon": report.pokemon, "walls": report.walls, "notes": report.notes,
            "moves": [_coverage_move_json(m) for m in report.moves]}


def _coverage_move_json(m: CoverageMove) -> dict:
    """JSON form of a coverage move: identity, power, class, the stat used, its multiplier on each wall, and
    how many walls it hits x2 (`hits`) and x1 (`neutral`).

    >>> m = _coverage_move_json(advisor.suggest("pikachu").moves[0])
    >>> m["name"], m["damage_class"].value, m["stat"], m["damage"], m["hits"]
    ('surf', 'special', 50, 4500.0, 1)
    """
    return {**ref_json(m.ref), "type": m.type, "power": m.power, "accuracy": m.accuracy, "pp": m.pp,
            "damage_class": m.damage_class, "stat": m.stat, "damage": round(m.damage, 1),
            "multipliers": m.multipliers, "hits": m.hits, "neutral": m.neutral}


class NoCacheStaticFiles(StaticFiles):
    """Static files the browser must revalidate on each load, so frontend edits show on a normal reload.

    Example: GET / -> 200 with "Cache-Control: no-cache" (304 if unchanged).
    """

    async def get_response(self, path, scope):
        """The usual static response, with `Cache-Control: no-cache` added."""
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


# Mounted last so /api/* routes take precedence. Without a build, the API still works on its own.
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if FRONTEND_DIR.is_dir():
    app.mount("/", NoCacheStaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    log.warning("No frontend/dist: run `npm install` and `npm run build` in frontend/ to get the page")
