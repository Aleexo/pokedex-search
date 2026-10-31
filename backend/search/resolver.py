"""Entity resolution: map a query to Pokémon, moves, abilities and types. Only NAMES are compared, never
descriptions or effects.

One name (`resolve`): one measure, the edit distance (OSA: a swap of two neighbouring letters counts as one typo)
between the query and the START of each name (the name cut to about the query's length), or of any word in it
("mime" -> mr mime). 0 means it starts with the query; 1-2 means a likely typo. The closest names are returned:
exact names first, then matches at the start of the name, then on a later word. If nothing is close enough,
nothing is returned.

Several names (`resolve_names`), for a query that is no single name ("raichu and pikachu"): a name of several
words is kept whole when written in full; every other word of 3+ letters gets its closest names, as above.
"""

from dataclasses import dataclass

from domain.repository import EntityRef, Repository
from search.normalize import normalize, osa_distance

MIN_PREFIX_LEN = 2
MIN_FUZZY_LEN = 3
MIN_FUZZY_LEN_IN_LIST = 6  # a name of several words inside a longer query: typos only from 6 letters


@dataclass(frozen=True)
class Candidate:
    """One entity a query could refer to, and how well it matched.

    >>> c = resolver.candidates("Bulbi")[0]
    >>> c.query, c.ref.name, c.distance, c.exact
    ('Bulbi', 'bulbasaur', 1, False)
    """

    query: str
    """The query as typed, before normalisation: the same for every candidate of one call."""
    ref: EntityRef
    """The entity whose name matched."""
    distance: int
    """Typos between the query and the start of the name (or of a word in it); 0 = prefix."""
    exact: bool
    """The query is the whole name."""
    at_start: bool
    """Matched at the start of the name, not on a later word."""

    @property
    def sort_key(self) -> tuple:
        """Best first: distance, then exact names, then start of the name; the ref makes ties deterministic.

        >>> [c.ref.name for c in sorted(resolver.candidates("mew"), key=lambda c: c.sort_key)]
        ['mew', 'mewtwo']
        """
        return (self.distance, not self.exact, not self.at_start, self.ref)


@dataclass(frozen=True)
class _Entry:
    """An entity in the index, with every point where a query may start matching its name.

    >>> next(e for e in resolver.entries if e.ref.name == "high-jump-kick").starts
    ('high jump kick', 'jump kick', 'kick')
    """

    ref: EntityRef
    """The entity it names."""
    starts: tuple[str, ...]
    """The normalised name from each of its words on; the first is the whole name."""


class EntityResolver:
    """Finds the entities whose name starts like the query, allowing a typo or two.

    >>> [c.ref.name for c in EntityResolver(repo).resolve("bulbi")]
    ['bulbasaur']
    """

    def __init__(self, repo: Repository):
        """Build the name index from every entity in the repository.

        >>> len(EntityResolver(repo).entries)  # Pokémon + moves + abilities + types
        447
        """
        self.entries = []
        for ref in repo.all_refs():
            words = normalize(ref.name).split()
            self.entries.append(_Entry(ref, tuple(" ".join(words[i:]) for i in range(len(words)))))

    def resolve(self, query: str) -> list[Candidate]:
        """The candidates at the smallest distance from the whole query, or [] if none is close.

        >>> [c.ref.name for c in resolver.resolve("thunder")][:2]
        ['thunder', 'thunder-punch']
        >>> [c.ref.name for c in resolver.resolve("mime")]
        ['mr-mime']
        >>> resolver.resolve("pikachu and raichu")
        []
        """
        return _best(self.candidates(query))

    def resolve_names(self, query: str) -> list[list[Candidate]]:
        """For a query that is no single name: the names it contains, read left to right.

        A name of several words is kept whole when it's written in full ("thunder wave", see `_full_distance`), the
        longest first. Every other word of 3 letters or more gets its closest matches, as if searched alone
        ("beam" -> the beams); a word that matches nothing ("and") is left aside.

        >>> [[c.ref.name for c in p] for p in resolver.resolve_names("raichu and pikachu")]
        [['raichu'], ['pikachu']]
        >>> [[c.ref.name for c in p] for p in resolver.resolve_names("pikachu thunder wave")]
        [['pikachu'], ['thunder-wave']]
        >>> [len(p) for p in resolver.resolve_names("beam and pikachu")]  # 5 beams, then Pikachu
        [5, 1]
        """
        words = normalize(query).split()
        pieces = []
        i = 0
        while i < len(words):
            piece = self._whole_name(words, i)
            if piece:  # a name of several words, written in full
                pieces.append(piece)
                i += len(piece[0].query.split())
                continue
            if len(words[i]) >= MIN_FUZZY_LEN:
                found = self.resolve(words[i])
                if found:
                    pieces.append(found)
            i += 1
        return pieces

    def _whole_name(self, words: list[str], i: int) -> list[Candidate]:
        """The longest name of several words that starts at word `i` and is written in full, or [].

        >>> [c.ref.name for c in resolver._whole_name(["thunder", "wave", "pikachu"], 0)]
        ['thunder-wave']
        """
        for j in range(len(words), i + 1, -1):  # the longest first; at least 2 words
            phrase = " ".join(words[i:j])
            found = []
            for entry in self.entries:
                distance = self._full_distance(phrase, entry.starts[0])
                if distance is not None:
                    found.append(Candidate(phrase, entry.ref, distance, distance == 0, True))
            if found:
                return _best(sorted(found, key=lambda c: c.sort_key))
        return []

    def candidates(self, query: str) -> list[Candidate]:
        """All candidates for one query, best first.

        >>> [c.ref.name for c in resolver.candidates("char")]
        ['charizard', 'charmander', 'charmeleon', 'cute-charm', 'harvest', 'harden', 'sharpen', 'chansey']
        """
        phrase = normalize(query)
        found = []
        for entry in self.entries:
            # (distance, at_start) from each start; index 0 is the whole name. Keep the best.
            options = [(self._distance(phrase, s), i == 0) for i, s in enumerate(entry.starts)]
            matched = [(d, at_start) for d, at_start in options if d is not None]
            if matched:
                distance, at_start = min(matched, key=lambda m: (m[0], not m[1]))
                found.append(Candidate(query, entry.ref, distance, phrase == entry.starts[0], at_start))
        return sorted(found, key=lambda c: c.sort_key)

    @staticmethod
    def _full_distance(phrase: str, name: str) -> int | None:
        """Distance between `phrase` and a whole normalised name, for a name of several words inside a longer
        query: 0 if equal, else typos from 6 letters only (1 at 6 letters, 2 above). No partial names here.

        >>> EntityResolver._full_distance("pikchu", "pikachu"), EntityResolver._full_distance("to", "toxic") is None
        (1, True)
        """
        if phrase == name:
            return 0
        if len(phrase) < MIN_FUZZY_LEN_IN_LIST:
            return None
        distance = osa_distance(phrase, name)
        return distance if distance <= (1 if len(phrase) == MIN_FUZZY_LEN_IN_LIST else 2) else None

    @staticmethod
    def _distance(phrase: str, name: str) -> int | None:
        """Edit distance between `phrase` and the start of one normalised name, or None if too far.

        >>> EntityResolver._distance("bulba", "bulbasaur")
        0
        >>> EntityResolver._distance("bulbi", "bulbasaur")
        1
        >>> EntityResolver._distance("bulbi", "vulpix") is None
        True
        >>> EntityResolver._distance("pichuka", "pikachu")  # letters swapped
        1
        >>> EntityResolver._distance("mow", "mew"), EntityResolver._distance("mow", "meowth") is None  # 3 letters: short names only
        (1, True)
        """
        n = len(phrase)
        if phrase == name or (n >= MIN_PREFIX_LEN and name.startswith(phrase)):
            return 0
        if n < MIN_FUZZY_LEN:
            return None
        # What the query is compared with. A 3-letter query: only a whole name of up to 4 letters (mow -> mew);
        # against the start of every name, one typo in 3 letters would match a dozen names. A longer query: the
        # start of the name, cut to its length ±1 for a missing or extra letter (bulbi -> bulba(saur), not vulpix).
        if n == MIN_FUZZY_LEN:
            parts = [name] if len(name) <= n + 1 else []
        else:
            parts = [name[:k].rstrip() for k in (n - 1, n, n + 1)]
        distances = [osa_distance(phrase, p) for p in parts]
        # Same letters in another order count as one typo (pichuka -> pikachu, where OSA gives 4). The first
        # letter must be right, or "team" would match "meta(pod)".
        distances += [1 for p in parts if p[:1] == phrase[:1] and sorted(p) == sorted(phrase)]
        allowed = 1 if n <= 6 else 2
        return min(distances) if distances and min(distances) <= allowed else None


def _best(candidates: list[Candidate]) -> list[Candidate]:
    """The candidates at the smallest distance (they come best first), or [] if there are none.

    >>> [c.ref.name for c in _best(resolver.candidates("mew"))]
    ['mew', 'mewtwo']
    """
    return [c for c in candidates if c.distance == candidates[0].distance] if candidates else []
