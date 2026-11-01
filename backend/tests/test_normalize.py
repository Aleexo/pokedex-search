import pytest
from rapidfuzz.distance import OSA

from search.names.normalize import normalize


@pytest.mark.parametrize("raw, expected", [
    ("Mr. Mime", "mr mime"),
    ("nidoran-m", "nidoran m"),
    ("Pokémon", "pokemon"),
    ("Farfetch'd", "farfetchd"),
    ("  SLEEP-POWDER  ", "sleep powder"),
])
def test_normalize(raw, expected):
    """Case, accents, punctuation and hyphens are normalised."""
    assert normalize(raw) == expected


def test_osa_distance():
    """Edit distances the resolver relies on (rapidfuzz's OSA): insert, delete, replace, and a swap of neighbours, 1 each."""
    assert OSA.distance("pikchu", "pikachu") == 1      # a missing letter
    assert OSA.distance("bulbi", "bulba") == 1         # a wrong letter
    assert OSA.distance("bulbi", "vulpi") == 2
    assert OSA.distance("", "abc") == 3
    assert OSA.distance("pikahcu", "pikachu") == 1     # two neighbours swapped (2 for plain Levenshtein)
    assert OSA.distance("chramandr", "charmande") == 2  # a swap plus a wrong letter
    assert OSA.distance("pichuka", "pikachu") == 4     # letters moved further: the resolver's reordering rule handles it

