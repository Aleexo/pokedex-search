from domain.repository import EntityRef, Kind
from explore import Explorer, Number, Order, tied_beyond


def _names(rows):
    """Row names, in order."""
    return [r.ref.name for r in rows]


def test_bar_chart_top_and_bottom(engine):
    """One number: the highest values first for 'top', the lowest first for 'bottom'."""
    explorer = Explorer(engine.repo)
    top = explorer.ranked(Number.SPEED, order=Order.TOP)
    bottom = explorer.ranked(Number.SPEED, order=Order.BOTTOM)
    assert _names(top)[:2] == ["electrode", "aerodactyl"]  # 150, then 130 (tied with Jolteon, Mewtwo: by name)
    assert _names(bottom)[0] == "slowpoke"  # 15
    assert [r.x for r in top] == sorted((r.x for r in top), reverse=True)


def test_groups_are_averaged(engine):
    """Grouped rows average their Pokémon: Dragon speed = (50 + 70 + 80) / 3."""
    rows = Explorer(engine.repo).ranked(Number.SPEED, by_type=True)
    dragon = next(r for r in rows if r.ref == EntityRef(Kind.TYPE, "dragon"))
    assert (dragon.x, dragon.count) == (66.7, 3)


def test_dual_type_pokemon_count_in_both_types(engine):
    """Bulbasaur (grass/poison) is counted in the Grass and the Poison rows."""
    rows = Explorer(engine.repo).ranked(Number.HP, by_type=True)
    counts = {r.ref.name: r.count for r in rows}
    expected = {t: sum(t in p.types for p in engine.repo.pokemon.values()) for t in ("grass", "poison")}
    assert counts["grass"] == expected["grass"] and counts["poison"] == expected["poison"]


def test_type_filter_keeps_any_of_the_types(engine):
    """Fire + Water keeps Pokémon with either type, and only them."""
    explorer = Explorer(engine.repo)
    kept = explorer.pokemon(frozenset({"fire", "water"}))
    expected = [p for p in engine.repo.pokemon.values() if {"fire", "water"} & set(p.types)]
    assert {p.name for p in kept} == {p.name for p in expected}


def test_filtered_ranking_only_uses_kept_pokemon(engine):
    """With a filter, every row comes from the kept Pokémon."""
    rows = Explorer(engine.repo).ranked(Number.SPEED, types=frozenset({"ghost"}))
    ghosts = {p.name for p in engine.repo.pokemon.values() if "ghost" in p.types}
    assert rows and {r.ref.name for r in rows} <= ghosts


def test_moves_are_ranked_on_their_own_power(engine):
    """A move field ranks moves on their own values: the most powerful first."""
    rows = Explorer(engine.repo).ranked(Number.POWER)[:8]
    expected = sorted(engine.repo.moves.values(), key=lambda m: (-(m.power or 0), m.name))[:8]
    assert [r.ref.name for r in rows] == [m.name for m in expected]
    assert rows[0].ref.name == "explosion" and rows[0].x == 250


def test_moves_without_a_value_are_left_out(engine):
    """Status moves have no power, so they are not in a power ranking, even at the bottom."""
    rows = Explorer(engine.repo).rows(Number.POWER)
    assert len(rows) == sum(m.power is not None for m in engine.repo.moves.values())
    assert "growl" not in {r.ref.name for r in rows}


def test_a_damaging_move_without_accuracy_counts_as_never_missing(engine):
    """Swift has no accuracy because it never misses: 100 in an accuracy ranking. Status moves without accuracy
    (Swords Dance, Splash…) are left out: accuracy doesn't apply to them."""
    rows = {r.ref.name: r.x for r in Explorer(engine.repo).rows(Number.ACCURACY)}
    assert rows["swift"] == 100
    assert "swords-dance" not in rows and "splash" not in rows


def test_type_filter_keeps_moves_of_those_types(engine):
    """With moves, the type filter uses the move's own type."""
    rows = Explorer(engine.repo).ranked(Number.POWER, types=frozenset({"fire"}))
    assert rows and all(engine.repo.moves[r.ref.name].type == "fire" for r in rows)


def test_the_field_decides_the_subject(engine):
    """The field decides the subject: move fields rank moves, the others Pokémon."""
    explorer = Explorer(engine.repo)
    assert {r.ref.kind for r in explorer.ranked(Number.POWER)} == {Kind.MOVE}
    assert {r.ref.kind for r in explorer.ranked(Number.SPEED)} == {Kind.POKEMON}


def test_moves_can_be_split_by_type(engine):
    """Moves grouped by type average the move field over the type's moves that have a value."""
    rows = Explorer(engine.repo).rows(Number.POWER, by_type=True)
    fire = next(r for r in rows if r.ref.name == "fire")
    powers = [m.power for m in engine.repo.moves.values() if m.type == "fire" and m.power is not None]
    assert (fire.x, fire.count) == (round(sum(powers) / len(powers), 1), len(powers))


def test_type_filter_and_grouping_by_type_are_exclusive(engine):
    """Filtering by type while grouping by type is refused, for Pokémon and for moves."""
    import pytest
    fire = frozenset({"fire"})
    for number in (Number.HP, Number.PP):
        with pytest.raises(ValueError):
            Explorer(engine.repo).rows(number, True, fire)


def test_rows_tied_with_the_last_shown_are_counted(engine):
    """Ties at the cut are reported, so a row left out only by name order isn't hidden silently."""
    ranked = Explorer(engine.repo).ranked(Number.POWER)
    last = ranked[7].x
    expected = sum(1 for r in ranked[8:] if r.x == last)
    assert tied_beyond(ranked) == expected and expected > 0  # several moves have 120 power
