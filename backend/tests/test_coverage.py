"""Move coverage: the Pokémon's moves of other types that get past its walls. Expected values were
computed by code independent of the module, from data/pokedex.json and data/type_chart.json."""

import pytest

from coverage import CoverageAdvisor, TypeChart


@pytest.fixture(scope="module")
def chart():
    """The committed type chart."""
    return TypeChart.from_data()


@pytest.fixture(scope="module")
def advisor(engine, chart):
    """An advisor over the real data."""
    return CoverageAdvisor(engine.repo, chart)


def test_type_chart_has_the_18_types_and_known_relations(chart):
    """The committed chart is complete and matches well-known relations."""
    assert len(chart.chart) == 18
    assert chart.multiplier("electric", "ground") == 0
    assert chart.multiplier("ground", "electric") == 2
    assert chart.multiplier("normal", "ghost") == 0
    assert chart.multiplier("fire", "grass") == 2
    assert chart.multiplier("fire", "normal") == 1


def test_walls_are_the_types_resisting_all_its_types(engine, advisor, chart):
    """Charizard: only Rock resists both Fire and Flying. Pikachu: Electric is resisted by Dragon, Electric, Grass
    and Ground (immune). Geodude (Rock / Ground): no type resists both, so it has no wall."""
    assert advisor.suggest("charizard").walls == ["rock"]
    assert advisor.suggest("pikachu").walls == ["dragon", "electric", "grass", "ground"]  # alphabetical
    assert advisor.suggest("geodude").walls == []
    for name, pokemon in engine.repo.pokemon.items():
        for w in advisor.suggest(name).walls:
            assert all(chart.multiplier(own, w) <= 0.5 for own in pokemon.types)


@pytest.mark.parametrize("name, moves", [  # (move, walls hit x2, walls hit x1)
    ("charizard", [("earthquake", 1, 0), ("dig", 1, 0), ("submission", 1, 0)]),  # its Fire / Flying moves left out
    ("pikachu", [("surf", 1, 1), ("skull-bash", 0, 4), ("double-edge", 0, 4), ("mega-kick", 0, 4), ("body-slam", 0, 4)]),
    ("snorlax", [("earthquake", 2, 1), ("submission", 2, 0), ("solar-beam", 1, 1), ("fire-blast", 1, 1), ("surf", 1, 2)]),
    ("bulbasaur", [("double-edge", 0, 1), ("body-slam", 0, 1), ("take-down", 0, 1), ("cut", 0, 1), ("tackle", 0, 1)]),
])
def test_widest_coverage(advisor, name, moves):
    """Moves of other types: first those hitting walls x2 (by how many, then damage), then those hitting walls
    only x1 (by how many, then damage). Bulbasaur had none before x1 counted: no move hits Poison or Steel x2."""
    assert [(m.ref.name, m.hits, m.neutral) for m in advisor.suggest(name).moves] == moves


def test_move_details(advisor):
    """Earthquake for Charizard: physical, so its Attack 84; x2 on its one wall, Rock."""
    eq = advisor.suggest("charizard").moves[0]
    assert (eq.type, eq.power, eq.accuracy, eq.pp) == ("ground", 100, 100, 10)
    assert (eq.damage_class.value, eq.stat, eq.damage) == ("physical", 84, 8400.0)
    assert (eq.multipliers, eq.hits, eq.neutral) == ({"rock": 2}, 1, 0)


def test_damage_uses_the_pokemons_matching_stat(advisor):
    """Pikachu's Surf (special): 90 power x 100 % x Sp. Atk 50 = 4500."""
    surf = advisor.suggest("pikachu").moves[0]
    assert (surf.ref.name, surf.stat, surf.damage) == ("surf", 50, 4500.0)


def test_no_wall_gives_an_empty_list_and_a_note(advisor):
    """Geodude (Rock / Ground): no type resists both of its types."""
    report = advisor.suggest("geodude")
    assert report.moves == [] and report.notes


def test_no_damaging_move(advisor):
    """Metapod learns no damaging move: empty list, with a note."""
    report = advisor.suggest("metapod")
    assert report.moves == [] and report.notes == ["This Pokémon learns no damaging move."]


def test_every_move_resisted_by_all_walls(advisor):
    """Butterfree: every damaging move of another type it learns is resisted by its wall (Steel): empty list, a note."""
    report = advisor.suggest("butterfree")
    assert report.walls and report.moves == []
    assert report.notes == ["All its walls resist every damaging move of another type it learns."]


def test_rules_hold_for_every_pokemon(engine, advisor, chart):
    """Learnable damaging moves of other types only, each hitting a wall x2 or x1; ranked; at most 5."""
    for name, pokemon in engine.repo.pokemon.items():
        report = advisor.suggest(name)
        for m in report.moves:
            record = engine.repo.moves[m.ref.name]
            assert m.ref.name in pokemon.moves and record.power is not None
            assert m.type not in pokemon.types  # no STAB
            assert m.pp == record.pp and m.damage_class is record.damage_class
            stat = pokemon.stats.attack if record.damage_class == "physical" else pokemon.stats.special_attack
            assert m.stat == stat and m.damage == m.power * (m.accuracy or 100) / 100 * stat
            assert m.multipliers == {w: chart.multiplier(m.type, w) for w in report.walls}
            assert m.hits == sum(1 for x in m.multipliers.values() if x >= 2)
            assert m.neutral == sum(1 for x in m.multipliers.values() if x == 1)
            assert m.hits + m.neutral >= 1
        assert len(report.moves) <= 5
        keys = [(0, -m.hits, -m.damage) if m.hits else (1, -m.neutral, -m.damage) for m in report.moves]
        assert keys == sorted(keys)


def test_unknown_pokemon(advisor):
    """An unknown name is a KeyError (404 in the API)."""
    with pytest.raises(KeyError):
        advisor.suggest("agumon")
