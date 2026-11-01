"""Text normalisation used by the resolver."""

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

