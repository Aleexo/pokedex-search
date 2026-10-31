"""Where the raw data comes from: JSON files in data/. The Repository only receives the dict read here."""

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def read_json(path: Path) -> dict[str, Any]:
    """Parse one JSON file, e.g. data/pokedex.json or data/type_chart.json.

    >>> sorted(read_json(DATA_DIR / "pokedex.json"))
    ['abilities', 'metadata', 'moves', 'pokemon']
    """
    with open(path, encoding="utf-8") as f:
        return json.load(f)
