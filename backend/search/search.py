"""Search engine: query (a name, maybe partial or misspelt, or several names) -> ranked hits, each with the reason
it matched.

Framework-agnostic: `SearchEngine.from_data().search("bulbi")` works from plain Python, tests,
or the API layer.
"""

from dataclasses import dataclass, field
from pathlib import Path

from domain.repository import EntityRef, Kind, Repository
from domain.sources import DATA_DIR, read_json
from search.resolver import Candidate, EntityResolver

EXACT_SCORE = 1.0
PREFIX_SCORE = 0.9
WORD_SCORE = 0.85  # a later word of the name starts with the query: "mime" -> Mr. Mime
TYPO_PENALTY = 0.1  # per edit

KIND_ORDER = {Kind.POKEMON: 0, Kind.MOVE: 1, Kind.ABILITY: 2, Kind.TYPE: 3}


@dataclass
class Hit:
    """One search result: an entity, its score and why it matched.

    >>> engine.search("pikachu").hits[0]
    Hit(ref=EntityRef(kind=<Kind.POKEMON: 'pokemon'>, name='pikachu'), score=1.0, reasons=['Name matches'])
    """

    ref: EntityRef
    """The matching entity."""
    score: float
    """1.0 exact, 0.9 prefix, 0.85 later word, minus 0.1 per typo."""
    reasons: list[str]
    """Why it matched, shown to the user: "Name starts with 'bulba'"."""


@dataclass
class SearchResponse:
    """Everything returned for one query.

    >>> [h.ref.kind.value for h in engine.search("psychic").hits]
    ['move', 'type']
    """

    query: str
    """The query as typed."""
    hits: list[Hit]
    """The matches, best first."""
    notes: list[str] = field(default_factory=list)
    """Messages for the user, e.g. when nothing matches."""


def display_name(name: str) -> str:
    """Human-readable name: 'thunder-wave' -> 'Thunder Wave'.

    >>> display_name("thunder-wave")
    'Thunder Wave'
    """
    return name.replace("-", " ").title()


class SearchEngine:
    """Name search over the dataset, usable without the web layer.

    >>> engine.search("bulbi").hits[0].ref.name
    'bulbasaur'
    """

    def __init__(self, repo: Repository, resolver: EntityResolver):
        """Use an existing repository and resolver, e.g. built from test data.

        >>> SearchEngine(repo, EntityResolver(repo)).search("mew").hits[0].ref.name
        'mew'
        """
        self.repo = repo
        self.resolver = resolver

    @classmethod
    def from_data(cls, data_dir: Path = DATA_DIR) -> "SearchEngine":
        """Build the engine from the bundled data directory.

        >>> SearchEngine.from_data().search("pikachu").hits[0].ref.name
        'pikachu'
        """
        repo = Repository(read_json(data_dir / "pokedex.json"))
        return cls(repo, EntityResolver(repo))

    def search(self, query: str, limit: int | None = None) -> SearchResponse:
        """The ranked hits of the query (at most `limit`, all if None). The whole query is read as one name; if it
        is none, as the names it contains, each with its own hits, in the order typed.

        >>> [h.ref.name for h in engine.search("char").hits]
        ['charmander', 'charmeleon', 'charizard', 'cute-charm']
        >>> [h.ref.name for h in engine.search("raichu and pikachu").hits]
        ['raichu', 'pikachu']
        """
        hits = sorted((self._hit(c) for c in self.resolver.resolve(query)), key=self._rank_key)
        if not hits:
            for piece in self.resolver.resolve_names(query):
                for hit in sorted((self._hit(c) for c in piece), key=self._rank_key):
                    if all(h.ref != hit.ref for h in hits):
                        hits.append(hit)
        return SearchResponse(
            query=query,
            hits=hits[:limit],
            notes=[] if hits else ["No match. Try a Pokémon, move, ability or type name."],
        )

    @staticmethod
    def _hit(c: Candidate) -> Hit:
        """A candidate as a hit: its score and the reason shown.

        >>> SearchEngine._hit(resolver.resolve("bulbi")[0])
        Hit(ref=EntityRef(kind=<Kind.POKEMON: 'pokemon'>, name='bulbasaur'), score=0.8, reasons=["Close to 'bulbi' (possible typo)"])
        """
        typed = c.query.strip()  # for the reason shown: the query as typed, without outer spaces
        base = PREFIX_SCORE if c.at_start else WORD_SCORE
        if c.exact:
            score, reason = EXACT_SCORE, "Name matches"
        elif c.distance > 0:
            score, reason = base - TYPO_PENALTY * c.distance, f"Close to '{typed}' (possible typo)"
        elif c.at_start:
            score, reason = base, f"Name starts with '{typed}'"
        else:
            score, reason = base, f"A word of the name starts with '{typed}'"
        return Hit(c.ref, round(score, 3), [reason])

    def _rank_key(self, hit: Hit) -> tuple:
        """Sort key: score, then kind, then Pokédex number, then name.

        >>> engine._rank_key(engine.search("pikachu").hits[0])
        (-1.0, 0, 25, 'pikachu')
        """
        record = self.repo.by_kind[hit.ref.kind][hit.ref.name]
        return (-hit.score, KIND_ORDER[hit.ref.kind], record.id, hit.ref.name)  # a type's id is 0
