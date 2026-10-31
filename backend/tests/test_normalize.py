import pytest

from search.normalize import normalize, osa_distance


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
    """Edit distances the resolver relies on: insert, delete, replace, and a swap of neighbours, 1 each."""
    assert osa_distance("pikchu", "pikachu") == 1      # a missing letter
    assert osa_distance("bulbi", "bulba") == 1         # a wrong letter
    assert osa_distance("bulbi", "vulpi") == 2
    assert osa_distance("", "abc") == 3
    assert osa_distance("pikahcu", "pikachu") == 1     # two neighbours swapped (2 for plain Levenshtein)
    assert osa_distance("chramandr", "charmande") == 2  # a swap plus a wrong letter
    assert osa_distance("pichuka", "pikachu") == 4     # letters moved further: the resolver's reordering rule handles it


def test_osa_distance_matches_a_full_table_implementation():
    """The three-row version gives the same values as the textbook full-table OSA, both ways round."""
    import random

    def full(a, b):
        d = [[i + j if i * j == 0 else 0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
        for i in range(1, len(a) + 1):
            for j in range(1, len(b) + 1):
                d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
                if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                    d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
        return d[-1][-1]

    rng = random.Random(0)
    for _ in range(2000):
        a = "".join(rng.choice("abc") for _ in range(rng.randint(0, 7)))
        b = "".join(rng.choice("abc") for _ in range(rng.randint(0, 7)))
        assert osa_distance(a, b) == osa_distance(b, a) == full(a, b), (a, b)
