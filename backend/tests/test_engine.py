from domain.repository import EntityRef, Kind


def test_exact_name_is_the_top_hit(engine):
    """An exact name scores 1.0 and ranks first."""
    response = engine.search("pikachu")
    assert response.hits[0].ref == engine.repo.ref(Kind.POKEMON, "pikachu")
    assert response.hits[0].score == 1.0


def test_typo_is_found_and_explained(engine):
    """A misspelt name is found despite the typo, and the reason says so."""
    hit = engine.search("pikchu").hits[0]
    assert hit.ref == engine.repo.ref(Kind.POKEMON, "pikachu")
    assert "typo" in hit.reasons[0]


def test_shared_name_gives_equal_hits(engine):
    """A name shared by two kinds returns both, with the same score."""
    hits = engine.search("psychic").hits
    assert {h.ref.kind for h in hits} == {Kind.TYPE, Kind.MOVE}
    assert hits[0].score == hits[1].score == 1.0


def test_exact_ranks_above_prefix(engine):
    """An exact match wins over names that only start with the query."""
    hits = engine.search("thunder").hits
    assert hits[0].ref == engine.repo.ref(Kind.MOVE, "thunder")
    assert all(h.score <= hits[0].score for h in hits)


def test_every_hit_has_a_reason(engine):
    """Every hit explains why it matched."""
    assert all(h.reasons for h in engine.search("char").hits)


def test_nonsense_gives_a_note(engine):
    """No match returns no hits and a note instead of an empty page."""
    response = engine.search("qwzx")
    assert response.hits == [] and response.notes


def _names(query, engine):
    """The names found for a query, in order."""
    return [h.ref.name for h in engine.search(query).hits]


def test_a_query_of_several_names_finds_each(engine):
    """A query that is no single name is read as the names it contains, in the order typed."""
    assert _names("raichu and pikachu", engine) == ["raichu", "pikachu"]
    assert _names("pikachu thunderbolt", engine) == ["pikachu", "thunderbolt"]
    typos = _names("pikchu thundr", engine)  # each word as if searched alone: "thundr" finds every Thunder move
    assert typos[0] == "pikachu" and set(typos[1:]) == {h.ref.name for h in engine.search("thundr").hits}
    assert _names("thunder wave pikachu", engine) == ["thunder-wave", "pikachu"]  # the longest name first


def test_each_word_gets_its_closest_matches(engine):
    """A partial word finds what it finds alone; a word that matches nothing ("and") or of under 3 letters is left
    aside."""
    assert _names("bulba pikachu", engine) == ["bulbasaur", "pikachu"]
    beams = _names("beam and pikachu", engine)
    assert beams[-1] == "pikachu" and set(beams[:-1]) == {h.ref.name for h in engine.search("beam").hits}
    assert _names("raichu to pikachu", engine) == ["raichu", "pikachu"]  # "to" alone would find Toxic…


def test_names_of_one_word_side_by_side_are_not_one_misspelt_name(engine):
    """`fire blaze` among other names is Fire and Blaze (each a name), not Fire Blast with 2 typos; a misspelt name
    whose words aren't all names stays whole (`thunder wabe` -> Thunder Wave)."""
    assert {"fire", "blaze"} <= set(_names("pikachu fire blaze", engine))
    assert _names("thunder wabe pikachu", engine) == ["thunder-wave", "pikachu"]


def test_a_kind_word_left_as_a_label_is_not_searched_as_a_name(engine):
    """`char pokemon`: pokemon is Charizard's label, so the name search answers, without reading `pokemon` as a name
    (it would add Porygon and the Poison moves)."""
    assert _names("char pokemon", engine) == ["charmander", "charmeleon", "charizard", "cute-charm"]
