"""Reading a relation query, in two steps: the query as items and kind words (`to_items`), then the groups they form
(`to_groups`). The rules are in docs/RELATION_SEARCH.md.
"""

from dataclasses import dataclass, field

from domain.repository import EntityRef, Kind, can_link
from search.names.resolver import MIN_FUZZY_LEN, EntityResolver, Piece

KIND_WORDS = {"pokemon": Kind.POKEMON, "move": Kind.MOVE, "ability": Kind.ABILITY, "type": Kind.TYPE}
"""One normalised word per kind; plurals match them with a typo or more (see `kind_of`)."""

Item = tuple[EntityRef, ...]
"""An item named in the query: the entities it may be, usually one (`psychic`: the move and the type)."""


@dataclass
class Group:
    """A kind word and the items it takes: its result is the entities of that kind linked to them.

    >>> group = Group(Kind.POKEMON, [(repo.ref(Kind.TYPE, "fire"),)])  # fire pokemon
    >>> group.kind, [[r.name for r in item] for item in group.items]
    (<Kind.POKEMON: 'pokemon'>, [['fire']])
    """

    kind: Kind
    """What the group returns."""
    items: list[Item] = field(default_factory=list)
    """The items filtering it."""


def to_items(query: str, resolver: EntityResolver) -> list[Item | Kind]:
    """The query as items (the entities each word or name of several words may be) and kind words, left to right;
    the kind words that only name the item next to them (labels: `ability blaze`) are dropped.

    >>> [[r.name for r in t] if isinstance(t, tuple) else t for t in to_items("Pikachu electric moves Types", resolver)]
    [['pikachu'], ['electric'], <Kind.MOVE: 'move'>, <Kind.TYPE: 'type'>]
    >>> [t if isinstance(t, Kind) else len(t) for t in to_items("fire pokemon ability blaze", resolver)]
    [1, <Kind.POKEMON: 'pokemon'>, 1]
    """
    tokens = [t.refs if isinstance(t, Piece) else t for t in resolver.resolve_names(query, special=kind_of)]
    return [t for i, t in enumerate(tokens) if not _is_label(tokens, i)]


def to_groups(items: list[Item | Kind]) -> list[Group] | None:
    """The groups the items form, in order; each group's result filters the next. Each kind word takes the items
    before it, the last one also those after. None without a kind word (the name search answers); [] when an item is
    left without a group (no results).

    >>> fire, blaze, fire_blast = (repo.ref(Kind.TYPE, "fire"),), (repo.ref(Kind.ABILITY, "blaze"),), (repo.ref(Kind.MOVE, "fire-blast"),)
    >>> show = lambda groups: [(g.kind.value, [r.name for item in g.items for r in item]) for g in groups]
    >>> show(to_groups([fire, Kind.POKEMON, blaze, fire_blast]))  # fire pokemon ability blaze and fire blast
    [('pokemon', ['fire', 'blaze', 'fire-blast'])]
    >>> show(to_groups([blaze, Kind.POKEMON, fire, Kind.MOVE]))  # blaze pokemon fire moves: Fire goes to moves
    [('pokemon', ['blaze']), ('move', ['fire'])]
    >>> to_groups([blaze, fire_blast]) is None, to_groups([(repo.ref(Kind.TYPE, "grass"),), Kind.MOVE, fire])
    (True, [])
    """
    if not any(isinstance(t, Kind) for t in items):
        return None
    groups: list[Group] = []
    pending: list[Item] = []
    for t in items:
        if not isinstance(t, Kind):
            pending.append(t)
            continue
        if groups:  # items between two kind words: to the one they can filter; if both, to the next
            back = [i for i in pending if not can_filter(i, t) and can_filter(i, groups[-1].kind)]
            if _repeats(groups[-1], back):
                return []
            groups[-1].items += back
            pending = [i for i in pending if i not in back]
        groups.append(Group(t, pending))
        pending = []
    if _repeats(groups[-1], pending):  # after the last kind word, an item of a kind its group already has
        return []
    groups[-1].items += pending
    return groups


def kind_of(word: str) -> Kind | None:
    """The kind a word names, matched against the kind words like a name (`EntityResolver.distance`: its start, or
    typos; from 7 letters up to 3, so that plurals fit: `abilities` is 3 from `ability`).

    >>> [kind_of(w) for w in ("abilities", "moves", "poke", "abilites", "typ", "more")]
    [<Kind.ABILITY: 'ability'>, <Kind.MOVE: 'move'>, <Kind.POKEMON: 'pokemon'>, <Kind.ABILITY: 'ability'>, <Kind.TYPE: 'type'>, <Kind.MOVE: 'move'>]
    >>> kind_of("over"), kind_of("abs"), kind_of("have")
    (None, None, None)
    """
    if len(word) < MIN_FUZZY_LEN:
        return None
    found = [(d, kind) for text, kind in KIND_WORDS.items() if (d := EntityResolver.distance(word, text)) is not None]
    return min(found)[1] if found else None


def can_filter(item: Item, kind: Kind) -> bool:
    """Whether one of the item's entities can be linked to entities of `kind`.

    >>> psychic = (repo.ref(Kind.MOVE, "psychic"), repo.ref(Kind.TYPE, "psychic"))
    >>> blaze = (repo.ref(Kind.ABILITY, "blaze"),)
    >>> can_filter(psychic, Kind.MOVE), can_filter(blaze, Kind.MOVE)  # Psychic is a type too
    (True, False)
    """
    return any(can_link(r.kind, kind) for r in item)


def _is_label(tokens: list[Item | Kind], i: int) -> bool:
    """Whether token `i` is a kind word naming the item next to it (`ability blaze`, `fire type`): that item is only
    of its kind, and no item before the kind word (since the previous one) could be filtered by it.

    >>> fire, blaze = (repo.ref(Kind.TYPE, "fire"),), (repo.ref(Kind.ABILITY, "blaze"),)
    >>> tokens = [fire, Kind.POKEMON, Kind.ABILITY, blaze]  # fire pokemon ability blaze
    >>> [_is_label(tokens, i) for i in range(len(tokens))]
    [False, False, True, False]
    """
    kind = tokens[i]
    if not isinstance(kind, Kind):
        return False
    start = max((j for j in range(i) if isinstance(tokens[j], Kind)), default=-1) + 1
    if any(not isinstance(t, Kind) and can_filter(t, kind) for t in tokens[start:i]):
        return False  # "pikachu moves thunder": moves takes Pikachu
    neighbours = [tokens[j] for j in (i - 1, i + 1) if 0 <= j < len(tokens)]
    return any(not isinstance(t, Kind) and all(r.kind is kind for r in t) for t in neighbours)


def _repeats(group: Group, items: list[Item]) -> bool:
    """Whether one of `items` is of a kind the group's items already have (`grass move fire`: two types).

    >>> grass, fire = (repo.ref(Kind.TYPE, "grass"),), (repo.ref(Kind.TYPE, "fire"),)
    >>> _repeats(Group(Kind.MOVE, [grass]), [fire])
    True
    """
    had = {r.kind for item in group.items for r in item}
    return any(r.kind in had for item in items for r in item)
