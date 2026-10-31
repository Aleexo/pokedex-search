from pathlib import Path

import pytest
import yaml

from search import SearchEngine

CASES_DIR = Path(__file__).parent / "cases"


def load_cases(filename: str) -> list:
    """Flatten `group: [case, ...]` into pytest params with readable ids."""
    with open(CASES_DIR / filename, encoding="utf-8") as f:
        groups = yaml.safe_load(f)
    return [pytest.param(case, id=f"{group}:{case['query']}") for group, cases in groups.items() for case in cases]


@pytest.fixture(scope="session")
def engine() -> SearchEngine:
    """One engine for the whole test session, since building it reads the dataset."""
    return SearchEngine.from_data()
