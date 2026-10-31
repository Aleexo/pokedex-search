import pytest

from domain.repository import EntityRef, Kind
from tests.conftest import load_cases


def _ref(text: str) -> EntityRef:
    """'kind:name' from a case file -> EntityRef."""
    kind, name = text.split(":", 1)
    return EntityRef(Kind(kind), name)


@pytest.mark.parametrize("case", load_cases("resolver.yaml"))
def test_resolver_case(engine, case):
    """Each labelled case puts the expected entity first, finds nothing, or finds all the listed ones."""
    found = [c.ref for c in engine.resolver.resolve(case["query"])]
    expect = case["expect"]

    if expect == "none":
        assert found == []
    elif isinstance(expect, list):
        assert {_ref(e) for e in expect} <= set(found), found
    else:
        assert found and found[0] == _ref(expect), found


def test_candidates_keep_the_query_as_typed(engine):
    """Each candidate records the query it was matched against, as typed (before normalisation)."""
    candidates = engine.resolver.resolve("  Bulbi ")
    assert candidates and all(c.query == "  Bulbi " for c in candidates)
    assert engine.search("  Bulbi ").hits[0].reasons == ["Close to 'Bulbi' (possible typo)"]
