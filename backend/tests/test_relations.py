import pytest

from domain.repository import EntityRef, Kind
from search.relations.headings import title
from tests.conftest import REPO, load_cases


def _ref(text: str) -> EntityRef:
    """'kind:name' from a case file -> EntityRef (cases name entities; the repository gives their id)."""
    kind, name = text.split(":", 1)
    return REPO.ref(Kind(kind), name)


@pytest.mark.parametrize("case", load_cases("relations.yaml"))
def test_relation_case(engine, case):
    """Each labelled case gives the expected lists, in order: heading, count and items (or the first ones); or no
    results; or, without a kind word, the name search's answer."""
    lists = engine.relations.search(case["query"])
    expect = case["expect"]

    if expect == "unchanged":
        assert lists is None
    elif expect == "none":
        assert lists == []
    else:
        assert [title(l) for l in lists] == [e["title"] for e in expect]
        for found, e in zip(lists, expect):
            assert len(found.refs) == e["count"], title(found)
            if "items" in e:
                assert found.refs == [_ref(r) for r in e["items"]]
            else:
                assert found.refs[:len(e["starts"])] == [_ref(r) for r in e["starts"]]


def test_hits_follow_the_lists(engine):
    """A relation search's hits are its lists one after the other, each hit marked with its list."""
    response = engine.search("blaze overgrow pokemon")
    assert [(h.ref.name, h.group) for h in response.hits] == [
        ("charmander", 0), ("charmeleon", 0), ("charizard", 0), ("bulbasaur", 1), ("ivysaur", 1), ("venusaur", 1)]


def test_no_results_gives_the_no_match_note(engine):
    """A relation query with no results says so, like the name search."""
    response = engine.search("grass move fire")
    assert response.hits == [] and response.notes


def test_cases_file_is_what_the_independent_script_writes():
    """relations.yaml holds what scripts/relation_cases.py computes from the data on its own, so the expected values
    can be recomputed: a hand edit that disagrees with the script fails here."""
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "scripts" / "relation_cases.py"
    spec = importlib.util.spec_from_file_location("relation_cases", path)
    assert spec and spec.loader
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    assert script.OUTPUT.read_text(encoding="utf-8") == script.yaml_text()
