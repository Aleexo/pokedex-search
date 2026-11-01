import re

import pytest
from fastapi.testclient import TestClient

from api.main import FRONTEND_DIR, app, repo

client = TestClient(app)
needs_build = pytest.mark.skipif(not FRONTEND_DIR.is_dir(), reason="frontend not built: npm run build in frontend/")


def test_search_returns_hits_with_reasons_and_pokemon_summary():
    """/api/search returns hits with reasons and Pokémon summaries."""
    body = client.get("/api/search", params={"q": "char"}).json()
    assert len(body["hits"]) >= 3 and all(h["reasons"] for h in body["hits"])
    assert {"height_m", "weight_kg", "stats"} <= set(body["hits"][0]["pokemon"])


def test_search_results_are_paged_like_all_pokemon(monkeypatch):
    """/api/search returns one page of hits with the page count and total, like /api/pokemon. With 5 per page,
    `po` (15 hits) gives 3 pages that, put together, are the whole ranked list; past the last page: 404."""
    whole = client.get("/api/search", params={"q": "po"}).json()
    assert (whole["page"], whole["pages"], whole["total"], len(whole["hits"])) == (1, 1, 15, 15)
    monkeypatch.setattr("api.main.PAGE_SIZE", 5)
    pages = [client.get("/api/search", params={"q": "po", "page": n}).json() for n in (1, 2, 3)]
    assert [p["pages"] for p in pages] == [3, 3, 3] and all(p["total"] == 15 for p in pages)
    assert [h["name"] for p in pages for h in p["hits"]] == [h["name"] for h in whole["hits"]]
    assert client.get("/api/search", params={"q": "po", "page": 4}).status_code == 404
    nothing = client.get("/api/search", params={"q": "qwzx"}).json()
    assert (nothing["pages"], nothing["total"], nothing["hits"]) == (1, 0, []) and nothing["notes"]


def test_relation_search_gives_headings_and_each_hits_list():
    """A relation query: `groups` holds each list's heading (text and entities with their card) and count; each hit
    has its list's index; all rows come on one page. A name search has no groups and no `group` on its hits."""
    body = client.get("/api/search", params={"q": "fire pokemon ability blaze"}).json()
    heading = body["groups"][0]["heading"]
    assert heading[0] == "Pokémon of type " and heading[1]["name"] == "fire" and heading[3]["short_effect"]
    assert body["groups"][0]["total"] == 3 and {h["group"] for h in body["hits"]} == {0}
    big = client.get("/api/search", params={"q": "psychic pokemon"}).json()  # 34 + 14 rows, folded: one page
    assert (big["pages"], big["total"], len(big["hits"])) == (1, 48, 48)
    names = client.get("/api/search", params={"q": "char"}).json()
    assert names["groups"] == [] and all("group" not in h for h in names["hits"])


def test_search_hits_carry_types_for_badges():
    """Pokémon and moves show type badges in the result list, so hits carry their types."""
    hits = {h["name"]: h for h in client.get("/api/search", params={"q": "thunder"}).json()["hits"]}
    assert hits["thunderbolt"]["types"] == ["electric"]
    assert client.get("/api/search", params={"q": "charizard"}).json()["hits"][0]["types"] == ["fire", "flying"]


def test_entity_pokemon_has_units_links_and_family():
    """Pokémon details use m and kg, and include abilities and the evolution family."""
    body = client.get("/api/entity/pokemon/bulbasaur").json()
    assert body["height_m"] == 0.7 and body["weight_kg"] == 6.9
    assert [p["name"] for p in body["evolution_family"]] == ["bulbasaur", "ivysaur", "venusaur"]
    assert any(a["name"] == "chlorophyll" for a in body["abilities"])


def test_entity_move_has_its_fields_and_learners():
    """Move details: type, power, class, and the Pokémon that learn it."""
    body = client.get("/api/entity/move/spore").json()
    assert (body["type"], body["power"], body["damage_class"]) == ("grass", None, "status")
    assert "paras" in [p["name"] for p in body["pokemon"]]


@needs_build
def test_frontend_is_served_from_the_same_process():
    """The built page and its script are served by the API process: no separate frontend server."""
    page = client.get("/")
    assert page.status_code == 200 and 'id="app"' in page.text
    script = re.search(r'src="(/assets/[^"]+\.js)"', page.text)
    assert script and client.get(script.group(1)).status_code == 200


@needs_build
def test_frontend_files_are_revalidated():
    """The browser must check the page on each load, so a new build is never hidden by a cached one."""
    assert client.get("/").headers["cache-control"] == "no-cache"


def test_unknown_entity_is_404():
    """Unknown name: 404. Invalid kind: 422, from the enum validation."""
    assert client.get("/api/entity/pokemon/agumon").status_code == 404
    assert client.get("/api/entity/digimon/agumon").status_code == 422  # invalid kind, rejected by the enum


def test_explore_returns_rows_with_labels_and_counts():
    """/api/explore returns up to 8 rows that the frontend can label and open."""
    body = client.get("/api/explore", params={"x": "speed", "by_type": True}).json()
    assert len(body["rows"]) == 8
    assert body["rows"][0] == {"kind": "type", "name": "electric", "label": "Electric", "x": 100.0, "count": 9,
                               "types": ["electric"]}


def test_explore_rows_carry_their_types_for_colouring():
    """Pokémon rows carry their type(s), so a dual-type Pokémon can be drawn in both colours."""
    rows = client.get("/api/explore", params={"x": "attack", "types": "fire"}).json()["rows"]
    charizard = next(r for r in rows if r["name"] == "charizard")
    assert charizard["types"] == ["fire", "flying"]


def test_explore_rejects_unknown_fields():
    """An unknown field, or no field, is a 422."""
    assert client.get("/api/explore", params={"x": "colour", "by_type": True}).status_code == 422
    assert client.get("/api/explore").status_code == 422


def test_explore_fields_lists_the_menus():
    """The menus come from the backend, so labels live in one place."""
    body = client.get("/api/explore/fields").json()
    assert {"name": "weight", "label": "Weight (kg)", "subject": "pokemon"} in body["numbers"]
    assert {"name": "power", "label": "Power", "subject": "move"} in body["numbers"]


def test_explore_filters_and_matched_count():
    """Filters are query parameters; `matched` counts the Pokémon that pass them."""
    body = client.get("/api/explore", params={"x": "speed", "types": ["fire", "water"]}).json()
    assert (body["matched"], body["total"], body["noun"]) == (44, 151, "Pokémon")
    assert client.get("/api/explore", params={"x": "speed", "types": "fairy-ish"}).status_code == 422


def test_explore_filter_offers_the_types_of_the_pokemon():
    """The type filter offers the types that some Pokémon has."""
    offered = {t["name"] for t in client.get("/api/explore/fields").json()["filters"]["types"]}
    assert offered == {t for p in repo.pokemon.values() for t in p.types}


def test_explore_field_gives_the_subject():
    """A move field ranks moves, a Pokémon field Pokémon; `by_type` groups either by type."""
    body = client.get("/api/explore", params={"x": "power"}).json()
    assert (body["subject"], body["by_type"]) == ("move", False)
    assert body["rows"][0]["name"] == "explosion" and body["noun"] == "moves" and body["total"] == 164
    by_type = client.get("/api/explore", params={"x": "power", "by_type": True}).json()
    assert by_type["rows"][0]["kind"] == "type" and by_type["subject"] == "move"
    assert client.get("/api/explore", params={"x": "speed"}).json()["subject"] == "pokemon"


def test_type_details_list_its_pokemon_and_moves():
    """A type's details list every Pokémon of that type and every move of that type (dataset order)."""
    body = client.get("/api/entity/type/electric").json()
    assert len(body["pokemon"]) == 9
    assert len(body["moves"]) == 5  # Gen 1 Electric moves
    assert {"thunderbolt", "thunder-wave"} <= {m["name"] for m in body["moves"]}


def test_explore_reports_ties():
    """The response says how many rows not shown tie with the 8th (several moves have 120 power)."""
    assert client.get("/api/explore", params={"x": "power"}).json()["tied_beyond"] > 0


def test_explore_refuses_type_filter_with_type_grouping():
    """One or the other: a type filter with group-by-type is a 422."""
    assert client.get("/api/explore", params={"x": "hp", "by_type": True, "types": "fire"}).status_code == 422


def test_coverage_route():
    """/api/coverage returns the walls, the moves with what a table line shows, and notes; 404 if unknown."""
    body = client.get("/api/coverage/charizard").json()
    assert (body["walls"], body["notes"]) == (["rock"], [])
    assert {"name", "type", "power", "accuracy", "pp", "damage_class", "stat", "multipliers", "hits", "neutral"} <= set(body["moves"][0])
    assert client.get("/api/coverage/agumon").status_code == 404


def test_pokemon_pages_list_all_pokemon_in_pokedex_order():
    """/api/pokemon: all 151 Pokémon, 20 per page, in Pokédex order, as result rows; 404 past the last page."""
    first = client.get("/api/pokemon").json()
    assert (first["page"], first["pages"], first["total"]) == (1, 8, 151)
    assert len(first["hits"]) == 20 and first["hits"][0]["name"] == "bulbasaur" and first["hits"][19]["name"] == "raticate"
    assert first["hits"][0]["types"] == ["grass", "poison"] and first["hits"][0]["pokemon"]["id"] == 1
    last = client.get("/api/pokemon", params={"page": 8}).json()
    assert len(last["hits"]) == 11 and last["hits"][0]["name"] == "kabutops" and last["hits"][-1]["name"] == "mew"
    assert client.get("/api/pokemon", params={"page": 9}).status_code == 404
    assert client.get("/api/pokemon", params={"page": 0}).status_code == 422


def test_pokemon_names_in_details_carry_their_summary():
    """Every Pokémon named in the details (an evolution family; the Pokémon of a move, an ability, a type) carries
    its types and sprite, for the card shown on hover."""
    family = client.get("/api/entity/pokemon/bulbasaur").json()["evolution_family"]
    assert [(p["name"], p["types"]) for p in family] == [
        ("bulbasaur", ["grass", "poison"]), ("ivysaur", ["grass", "poison"]), ("venusaur", ["grass", "poison"])]
    assert all(p["sprite"].startswith("https://") for p in family)
    for kind, name in (("move", "spore"), ("ability", "overgrow"), ("type", "fire")):
        pokemon = client.get(f"/api/entity/{kind}/{name}").json()["pokemon"]
        assert pokemon and all({"types", "sprite"} <= set(p) for p in pokemon)


def test_move_names_in_details_carry_type_and_power():
    """Every move named in the details (a Pokémon's moves, a type's moves) carries its type, class and power (None
    for a status move), for the card shown on hover."""
    moves = {m["name"]: m for m in client.get("/api/entity/pokemon/bulbasaur").json()["moves"]}
    assert (moves["vine-whip"]["type"], moves["vine-whip"]["damage_class"], moves["vine-whip"]["power"]) == ("grass", "physical", 45)
    assert (moves["growl"]["type"], moves["growl"]["damage_class"], moves["growl"]["power"]) == ("normal", "status", None)
    electric = client.get("/api/entity/type/electric").json()["moves"]
    assert all(m["type"] == "electric" for m in electric) and {"power"} <= set(electric[0])

