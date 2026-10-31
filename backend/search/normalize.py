"""Text normalisation and string-distance helpers used by the resolver."""

import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")
_SPACES = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Lowercase, strip accents and punctuation, treat hyphens/underscores as spaces.

    >>> normalize("Mr. Mime")
    'mr mime'
    >>> normalize("Farfetch'd")
    'farfetchd'
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("'", "").replace("’", "")  # removed, not spaced: farfetch'd -> farfetchd
    text = _NON_ALNUM.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def osa_distance(a: str, b: str) -> int:
    """Edit distance where inserting, deleting or replacing a letter costs 1, and so does swapping two
    neighbouring letters (Optimal String Alignment, a Damerau-Levenshtein variant). Keeps three rows of the table.

    >>> osa_distance("pikchu", "pikachu"), osa_distance("pikahcu", "pikachu")  # a missing letter; a swap
    (1, 1)
    """
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    before: list[int] = []                 # the row two above the current one
    previous = list(range(len(b) + 1))     # the row just above
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            cost = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb))
            if i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:  # the last two letters swapped
                cost = min(cost, before[j - 2] + 1)
            current.append(cost)
        before, previous = previous, current
    return previous[-1]
