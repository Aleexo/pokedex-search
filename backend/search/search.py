"""Search engine: query (a name, maybe partial or misspelt, or several names) -> ranked hits, each with the reason
it matched; or, when the query has a kind word (`poison moves`), the relation search's lists.

Framework-agnostic: `SearchEngine.from_data().search("bulbi")` works from plain Python, tests,
or the API layer.
"""

from dataclasses import dataclass, field
from pathlib import Path

from domain.repository import EntityRef, Kind, Repository
from domain.sources import DATA_DIR, read_json
from search.names.resolver import Candidate, EntityResolver, Piece
from search.relations.reader import kind_of
from search.relations.relations import RelationSearch, ResultList

EXACT_SCORE = 1.0
PREFIX_SCORE = 0.9
WORD_SCORE = 0.85  # a later word of the name starts with the query: "mime" -> Mr. Mime
TYPO_PENALTY = 0.1  # per edit

NO_MATCH = "No match. Try a Pokémon, move, ability or type name."
KIND_ORDER = {Kind.POKEMON: 0, Kind.MOVE: 1, Kind.ABILITY: 2, Kind.TYPE: 3}


@dataclass
class Hit:
    """One search result: an entity, its score and why it matched.

    >>> engine.search("pikachu").hits[0]
    Hit(ref=EntityRef(kind=<Kind.POKEMON: 'pokemon'>, id=25, name='pikachu'), score=1.0, reasons=['Name matches'], group=None)
    """

    ref: EntityRef
    """The matching entity."""
    score: float | None
    """1.0 exact, 0.9 prefix, 0.85 later word, minus 0.1 per typo; None in a relation list (its heading says why)."""
    reasons: list[str]
    """Why it matched, shown to the user: "Name starts with 'bulba'"."""
    group: int | None = None
    """In a relation search, the index of its list in `SearchResponse.lists`."""


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
    lists: list[ResultList] = field(default_factory=list)
    """A relation search's lists, with their headings; empty for a name search."""


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
        self.relations = RelationSearch(repo, resolver)

    @classmethod
    def from_data(cls, data_dir: Path = DATA_DIR) -> "SearchEngine":
        """Build the engine from the bundled data directory.

        >>> SearchEngine.from_data().search("pikachu").hits[0].ref.name
        'pikachu'
        """
        repo = Repository(read_json(data_dir / "pokedex.json"))
        return cls(repo, EntityResolver(repo))

    def search(self, query: str, limit: int | None = None) -> SearchResponse:
        """The ranked hits of the query (at most `limit`, all if None). With a kind word, the relation search's lists,
        one after the other. Otherwise the whole query is read as one name; if it is none, as the names it contains,
        each with its own hits, in the order typed.

        >>> [h.ref.name for h in engine.search("char").hits]
        ['charmander', 'charmeleon', 'charizard', 'cute-charm']
        >>> [h.ref.name for h in engine.search("raichu and pikachu").hits]
        ['raichu', 'pikachu']
        >>> r = engine.search("charizard abilities")
        >>> [[f.name for f in l.filters] for l in r.lists], [(h.ref.name, h.group) for h in r.hits]
        ([['charizard']], [('blaze', 0), ('solar-power', 0)])
        """
        lists = self.relations.search(query)
        if lists is not None:
            hits = [Hit(ref, None, [], i) for i, found in enumerate(lists) for ref in found.refs]
            return SearchResponse(query, hits[:limit], [] if hits else [NO_MATCH], lists)
        hits = sorted((self._hit(c) for c in self.resolver.resolve(query)), key=self._rank_key)
        if not hits:
            for piece in self.resolver.resolve_names(query, special=kind_of):  # a kind word is never a name
                if not isinstance(piece, Piece):
                    continue
                for hit in sorted((self._hit(c) for c in piece.candidates), key=self._rank_key):
                    if all(h.ref != hit.ref for h in hits):
                        hits.append(hit)
        return SearchResponse(
            query=query,
            hits=hits[:limit],
            notes=[] if hits else [NO_MATCH],
        )

    @staticmethod
    def _hit(c: Candidate) -> Hit:
        """A candidate as a hit: its score and the reason shown.

        >>> SearchEngine._hit(Candidate("bulbi", repo.ref(Kind.POKEMON, "bulbasaur"), distance=1, exact=False, at_start=True))
        Hit(ref=EntityRef(kind=<Kind.POKEMON: 'pokemon'>, id=1, name='bulbasaur'), score=0.8, reasons=["Close to 'bulbi' (possible typo)"], group=None)
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
        """Sort key: score, then kind, then number (Pokédex number for a Pokémon).

        >>> engine._rank_key(Hit(repo.ref(Kind.POKEMON, "pikachu"), 1.0, ["Name matches"]))
        (-1.0, 0, 25)
        """
        return (-(hit.score or 0), KIND_ORDER[hit.ref.kind], hit.ref.id)
