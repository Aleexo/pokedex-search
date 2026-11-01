"""Names available to the usage examples (doctests) in the docstrings."""

import pytest

from coverage import CoverageAdvisor, TypeChart
from domain.records import DamageClass
from domain.repository import EntityRef, Kind, Repository
from explore import Explorer, Number, Order, Subject
from domain.sources import DATA_DIR, read_json
from search import SearchEngine
from search.names.resolver import EntityResolver


@pytest.fixture(autouse=True, scope="session")
def _doctest_names(doctest_namespace):
    """Give every docstring example `repo`, `resolver`, `engine`, `relations`, `explorer`, `chart`, `advisor` and the common imports.

    >>> engine.search("pikachu").hits[0].ref.name
    'pikachu'
    """
    engine = SearchEngine.from_data()
    chart = TypeChart.from_data()
    doctest_namespace.update(
        engine=engine, repo=engine.repo, resolver=engine.resolver, relations=engine.relations,
        EntityRef=EntityRef, Kind=Kind, DamageClass=DamageClass, Repository=Repository, EntityResolver=EntityResolver,
        SearchEngine=SearchEngine, read_json=read_json, DATA_DIR=DATA_DIR,
        explorer=Explorer(engine.repo), Explorer=Explorer, Subject=Subject, Number=Number, Order=Order,
        chart=chart, advisor=CoverageAdvisor(engine.repo, chart), TypeChart=TypeChart, CoverageAdvisor=CoverageAdvisor,
    )
