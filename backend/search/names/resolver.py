"""Entity resolution: map a query to Pokémon, moves, abilities and types. Only NAMES are compared, never
descriptions or effects.

One name (`resolve`): one measure, the edit distance (OSA, from rapidfuzz: a swap of two neighbouring letters
counts as one typo) between the query and the START of each name (the name cut to about the query's length), or
of any word in it ("mime" -> mr mime). 0 means it starts with the query; 1-2 means a likely typo. The closest names are returned:
exact names first, then matches at the start of the name, then on a later word. If nothing is close enough,
nothing is returned.

Several names (`resolve_names`), for a query that is no single name ("raichu and pikachu"): a name of several
words is kept whole when written in full; every other word of 3+ letters gets its closest names, as above. Each
is a `Piece`; a caller can also have special words kept as they are (the relation search's kind words).
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from rapidfuzz.distance import OSA

from domain.repository import EntityRef, Repository
from search.names.normalize import normalize

MIN_PREFIX_LEN = 2
MIN_FUZZY_LEN = 3
MIN_FUZZY_LEN_IN_LIST = 6  # a name of several words inside a longer query: typos only from 6 letters

T = TypeVar("T")  # what a caller's special words stand for (see `resolve_names`)


def typos_allowed(length: int) -> int:
    """How many typos a query word of `length` letters may have: 1 up to 6 letters, 3 from 7 (a plural fits:
    abilities -> ability). The rule of the name search and of the relation search's kind words. Names of several
    words inside a longer query stay stricter (`_full_distance`).

    >>> typos_allowed(5), typos_allowed(7)
    (1, 3)
    """
    return 1 if length <= 6 else 3


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
        """Best first: distance, then exact names, then start of the name; kind and name make ties deterministic.

        >>> [c.ref.name for c in sorted(resolver.candidates("mew"), key=lambda c: c.sort_key)]
        ['mew', 'mewtwo']
        """
        return (self.distance, not self.exact, not self.at_start, self.ref.kind, self.ref.name)


@dataclass(frozen=True)
class Piece:
    """A part of a query naming one thing: its words, and the closest names (`Candidate`s) it may be.

    >>> p = Piece("rock", tuple(resolver.resolve("rock")))  # the word and its closest names
    >>> p.text, len(p.candidates), [r.name for r in p.refs]
    ('rock', 4, ['rock'])
    """

    text: str
    """Its normalised words: "fire blast"."""
    candidates: tuple[Candidate, ...]
    """Its closest names, best first."""

    @property
    def refs(self) -> tuple[EntityRef, ...]:
        """Its entities: the exact names if any (`rock` → the type, not Rock Head; `psychic` → the type and the move),
        else the closest to the full name (`posion` → the Poison type, not Poison Point; `char` → Charizard).

        >>> [[r.name for r in Piece(w, tuple(resolver.resolve(w))).refs] for w in ("rock", "posion", "char")]
        [['rock'], ['poison'], ['charizard']]
        """
        exact = tuple(c.ref for c in self.candidates if c.exact)
        if exact:
            return exact
        full = {c.ref: OSA.distance(self.text, normalize(c.ref.name)) for c in self.candidates}
        return tuple(r for r, d in full.items() if d == min(full.values()))


def _no_special(word: str) -> None:
    """No special words: every word is looked up as a name."""
    return None


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
        self.names = {e.starts[0] for e in self.entries}  # every whole normalised name: "fire", "fire blast"

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

    def resolve_names(self, query: str, special: Callable[[str], T | None] = _no_special) -> list[Piece | T]:
        """For a query that is no single name: the names it contains, read left to right.

        A name of several words is kept whole when it's written in full ("thunder wave", see `_full_distance`), the
        longest first. Then a word that `special` recognises, unless it is a name itself ("agility" is a move), is kept
        as what it returns (the relation search's kind words). Every other word of 3 letters or more gets its closest matches, as if searched alone ("beam" -> the
        beams); a word that matches nothing ("and") is left aside.

        >>> [[r.name for r in p.refs] for p in resolver.resolve_names("raichu and pikachu")]
        [['raichu'], ['pikachu']]
        >>> [p.text for p in resolver.resolve_names("pikachu thunder wave")]
        ['pikachu', 'thunder wave']
        >>> [len(p.candidates) for p in resolver.resolve_names("beam and pikachu")]  # 5 beams, then Pikachu
        [5, 1]
        >>> resolver.resolve_names("mirror move pokemon", special=lambda w: w.upper() if w == "pokemon" else None)
        [Piece(text='mirror move', ...), 'POKEMON']
        """
        words = normalize(query).split()
        pieces: list[Piece | T] = []
        i = 0
        while i < len(words):
            whole = self.whole_name(words, i)
            if whole:  # a name of several words, written in full ("mirror move" stays a move)
                pieces.append(Piece(whole[0].query, tuple(whole)))
                i += len(whole[0].query.split())
                continue
            if words[i] not in self.names and (kept := special(words[i])) is not None:  # an exact name wins
                pieces.append(kept)
            elif len(words[i]) >= MIN_FUZZY_LEN:
                found = self.resolve(words[i])
                if found:
                    pieces.append(Piece(words[i], tuple(found)))
            i += 1
        return pieces

    def whole_name(self, words: list[str], i: int) -> list[Candidate]:
        """The longest name of several words that starts at word `i` and is written in full, or []. A misspelt one
        loses when each of its words is a name on its own ("fire blaze": Fire and Blaze, not Fire Blast).

        >>> [c.ref.name for c in resolver.whole_name(["thunder", "wave", "pikachu"], 0)]
        ['thunder-wave']
        >>> resolver.whole_name(["fire", "blaze"], 0), [c.ref.name for c in resolver.whole_name(["thunder", "wabe"], 0)]
        ([], ['thunder-wave'])
        """
        for j in range(len(words), i + 1, -1):  # the longest first; at least 2 words
            phrase = " ".join(words[i:j])
            found = []
            for entry in self.entries:
                distance = self._full_distance(phrase, entry.starts[0])
                if distance is not None:
                    found.append(Candidate(phrase, entry.ref, distance, distance == 0, True))
            best = _best(sorted(found, key=lambda c: c.sort_key))
            if best and (best[0].exact or not all(w in self.names for w in words[i:j])):
                return best
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
            options = [(self.distance(phrase, s), i == 0) for i, s in enumerate(entry.starts)]
            matched = [(d, at_start) for d, at_start in options if d is not None]
            if matched:
                distance, at_start = min(matched, key=lambda m: (m[0], not m[1]))
                found.append(Candidate(query, entry.ref, distance, phrase == entry.starts[0], at_start))
        return sorted(found, key=lambda c: c.sort_key)

    @staticmethod
    def _full_distance(phrase: str, name: str) -> int | None:
        """Distance between `phrase` and a whole normalised name, for a name of several words inside a longer
        query: 0 if equal, else typos from 6 letters only, 1 at 6 letters, 2 above. Stricter than `typos_allowed`
        on purpose: these phrases are cut from a sentence, and at 3 typos "and fire" (from "blaze and fire blast")
        would be Sand Force. No partial names here.

        >>> EntityResolver._full_distance("pikchu", "pikachu"), EntityResolver._full_distance("to", "toxic") is None
        (1, True)
        """
        if phrase == name:
            return 0
        if len(phrase) < MIN_FUZZY_LEN_IN_LIST:
            return None
        distance = OSA.distance(phrase, name)
        return distance if distance <= (1 if len(phrase) == MIN_FUZZY_LEN_IN_LIST else 2) else None

    @staticmethod
    def distance(phrase: str, name: str) -> int | None:
        """Edit distance between `phrase` and the start of one normalised name, or None if too far: the typo rule
        shared by the name search and the relation search's kind words (`reader.kind_of`).

        >>> EntityResolver.distance("bulba", "bulbasaur")
        0
        >>> EntityResolver.distance("bulbi", "bulbasaur")
        1
        >>> EntityResolver.distance("bulbi", "vulpix") is None
        True
        >>> EntityResolver.distance("pichuka", "pikachu")  # letters swapped
        1
        >>> EntityResolver.distance("mow", "mew"), EntityResolver.distance("mow", "meowth") is None  # 3 letters: short names only
        (1, True)
        >>> EntityResolver.distance("abilities", "ability")  # from 7 letters, up to 3 typos
        3
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
        distances = [OSA.distance(phrase, p) for p in parts]
        # Same letters in another order count as one typo (pichuka -> pikachu, where OSA gives 4). The first
        # letter must be right, or "team" would match "meta(pod)".
        distances += [1 for p in parts if p[:1] == phrase[:1] and sorted(p) == sorted(phrase)]
        return min(distances) if distances and min(distances) <= typos_allowed(n) else None


def _best(candidates: list[Candidate]) -> list[Candidate]:
    """The candidates at the smallest distance (they come best first), or [] if there are none.

    >>> [c.ref.name for c in _best(resolver.candidates("mew"))]
    ['mew', 'mewtwo']
    """
    return [c for c in candidates if c.distance == candidates[0].distance] if candidates else []
