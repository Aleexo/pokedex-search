"""Fetch the type relations from PokeAPI once and write them to data/type_chart.json.

The app never calls PokeAPI: it reads the committed file, so it runs offline. Run this script only to
refresh the chart (standard library only, no dependency):

    python scripts/fetch_type_chart.py          # from pokedex-search/

Source: GET https://pokeapi.co/api/v2/type/ lists the types; GET https://pokeapi.co/api/v2/type/{name},
field `damage_relations`, gives each type's latest relations (not `past_damage_relations`). Types without any
damage relation are skipped: `stellar`, `unknown` and `shadow` are not battle types, which leaves the 18.

Output: {"source", "fetched", "chart": {attacking type: {defending type: multiplier}}}, where only
multipliers other than 1 are stored (2, 0.5 or 0).
"""

import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

TYPE_ENDPOINT = "https://pokeapi.co/api/v2/type/"
TYPE_LIST_URL = TYPE_ENDPOINT + "?limit=100"  # every type, in one page
TYPE_DETAIL_URL = TYPE_ENDPOINT + "{name}"     # one type, with its damage relations
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "type_chart.json"

# PokeAPI field -> damage multiplier dealt by the attacking type.
MULTIPLIERS = {"double_damage_to": 2, "half_damage_to": 0.5, "no_damage_to": 0}


def get_json(url: str) -> dict:
    """GET a PokeAPI URL and parse the JSON body.

    Example (needs network): get_json(TYPE_LIST_URL)["count"] -> 21
    """
    request = urllib.request.Request(url, headers={"User-Agent": "pokedex-search/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def list_types(get=get_json) -> list[str]:
    """Names of all the types PokeAPI knows, including non-battle ones (stellar, unknown, shadow).

    >>> list_types(get=lambda url: {"results": [{"name": "fire"}, {"name": "shadow"}]})
    ['fire', 'shadow']
    """
    return [t["name"] for t in get(TYPE_LIST_URL)["results"]]


def fetch_relations(name: str, get=get_json) -> dict[str, float]:
    """Multipliers dealt by one attacking type (only those other than 1); empty for a non-battle type.

    >>> rel = {"double_damage_to": [{"name": "grass"}], "half_damage_to": [], "no_damage_to": []}
    >>> fetch_relations("fire", get=lambda url: {"damage_relations": rel})
    {'grass': 2}
    """
    relations = get(TYPE_DETAIL_URL.format(name=name))["damage_relations"]
    return {target["name"]: factor for field, factor in MULTIPLIERS.items() for target in relations[field]}


def build_chart(names: list[str], fetch=fetch_relations) -> tuple[dict[str, dict[str, float]], list[str]]:
    """The chart over the battle types, and the types skipped because they have no damage relation.

    >>> fake = {"fire": {"grass": 2, "fire": 0.5}, "grass": {"fire": 0.5}, "stellar": {}}
    >>> build_chart(["fire", "grass", "stellar"], fetch=lambda t: fake[t])
    ({'fire': {'fire': 0.5, 'grass': 2}, 'grass': {'fire': 0.5}}, ['stellar'])
    """
    relations = {name: fetch(name) for name in names}
    battle = sorted(name for name, row in relations.items() if row)
    skipped = sorted(name for name, row in relations.items() if not row)
    chart = {a: {d: relations[a][d] for d in sorted(relations[a]) if d in battle} for a in battle}
    return chart, skipped


def main() -> int:
    """Fetch and write the chart; print a short summary."""
    names = list_types()
    print(f"Fetching {len(names)} types from PokeAPI...")
    chart, skipped = build_chart(names)
    print(f"Skipped (no damage relation): {', '.join(skipped) or 'none'}")
    payload = {"source": TYPE_DETAIL_URL + " (damage_relations)", "fetched": date.today().isoformat(), "chart": chart}
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    relations = sum(len(row) for row in chart.values())
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(chart)} types, {relations} relations other than x1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
