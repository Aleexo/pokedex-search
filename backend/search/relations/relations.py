"""Relation search: the entities of the kind asked for, linked to everything the query names, in lists. Each list
says what it is (its kind, its filters, the list it follows); its wording is built at the end (headings.py). The
rules are in docs/RELATION_SEARCH.md.
"""

from collections import defaultdict
from dataclasses import dataclass
from itertools import product

from domain.repository import EntityRef, Kind, Repository, can_link
from search.names.resolver import EntityResolver
from search.relations.reader import Group, to_groups, to_items


@dataclass
class ResultList:
    """One list of results and what it is: the entities of `kind` linked to every filter and, in a chain, to any
    entity of the list it follows.

    >>> charizard = repo.ref(Kind.POKEMON, "charizard")
    >>> blaze_pokemon = ResultList(Kind.POKEMON, (repo.ref(Kind.ABILITY, "blaze"),), None, [charizard])
    >>> ResultList(Kind.MOVE, (repo.ref(Kind.TYPE, "fire"),), blaze_pokemon, []).chain.refs  # Fire moves of Blaze Pokémon
    [EntityRef(kind=<Kind.POKEMON: 'pokemon'>, id=6, name='charizard')]
    """

    kind: Kind
    """What the list holds."""
    filters: tuple[EntityRef, ...]
    """The entities named in its group; each of its entities is linked to all of them: Fire, Blaze."""
    chain: "ResultList | None"
    """The previous group's list it follows; each of its entities is linked to one of that list's at least."""
    refs: list[EntityRef]
    """The entities, by number."""


class RelationSearch:
    """The lists of entities linked to what a query names.

    >>> [(l.kind, [f.name for f in l.filters], len(l.refs)) for l in RelationSearch(repo, resolver).search("poison moves")]
    [(<Kind.MOVE: 'move'>, ['poison'], 8)]
    """

    def __init__(self, repo: Repository, resolver: EntityResolver):
        """Search over the repository's links, reading queries with the name resolver."""
        self.repo = repo
        self.resolver = resolver

    def search(self, query: str) -> list[ResultList] | None:
        """The non-empty lists for the query, in order. None when it has no kind word (the name search answers).

        >>> [[f.name for f in l.filters] for l in RelationSearch(repo, resolver).search("blaze overgrow pokemon")]
        [['blaze'], ['overgrow']]
        >>> RelationSearch(repo, resolver).search("pikachu thunderbolt") is None
        True
        """
        groups = to_groups(to_items(query, self.resolver))
        if groups is None:
            return None
        lists: list[ResultList] = []
        for i, group in enumerate(groups):
            found = self._group(group, lists if i else None)
            if found is None:  # an item that can't filter its group
                return []
            lists = found
        return [l for l in lists if l.refs]

    def _group(self, group: Group, previous: list[ResultList] | None) -> list[ResultList] | None:
        """Turn one group into its result lists.

        A group is a kind word and its items: `fire water pokemon blaze` is Group(POKEMON, [Fire, Water, Blaze]).
        It gives one list per way of reading it:
        - items of different kinds go in the same list, all must hold (and): Fire with Blaze;
        - items of the same kind go in different lists (or): Fire in one, Water in the other;
        - an item that is several entities goes in different lists: `psychic`, the move in one, the type in the other;
        - in a chain, each list of the previous group gives its own list, which follows it.
        So `fire water pokemon blaze` gives two lists: Fire Pokémon with Blaze, Water Pokémon with Blaze.

        Each item first keeps only the entities that can filter the group's kind (`snorlax moves psychic`: the type,
        as a move can't filter moves). If none can, the group can't be read: None (`blaze moves`).

        >>> fire, water, blaze = (repo.ref(Kind.TYPE, "fire"),), (repo.ref(Kind.TYPE, "water"),), (repo.ref(Kind.ABILITY, "blaze"),)
        >>> [[f.name for f in l.filters] for l in relations._group(Group(Kind.POKEMON, [fire, water, blaze]), None)]
        [['fire', 'blaze'], ['water', 'blaze']]
        >>> psychic = (repo.ref(Kind.MOVE, "psychic"), repo.ref(Kind.TYPE, "psychic"))  # one word, two entities
        >>> [[f.kind.value for f in l.filters] for l in relations._group(Group(Kind.POKEMON, [psychic]), None)]
        [['move'], ['type']]
        >>> relations._group(Group(Kind.MOVE, [blaze]), None) is None  # an ability doesn't filter moves
        True
        """
        choices = []
        for item in group.items:
            refs = [r for r in item if can_link(r.kind, group.kind)]
            if not refs:
                return None
            choices.append(refs)
        lists: list[ResultList] = []
        for reading in product(*choices):
            by_kind: dict[Kind, list[EntityRef]] = defaultdict(list)
            for ref in reading:
                if ref not in by_kind[ref.kind]:
                    by_kind[ref.kind].append(ref)
            # Items of the same kind: one list each (or); of different kinds: all must hold (and).
            for filters in product(*by_kind.values()):
                for chain in previous if previous is not None else [None]:
                    if not any(set(l.filters) == set(filters) and l.chain is chain for l in lists):
                        lists.append(self._list(group.kind, filters, chain))
        return lists

    def _list(self, kind: Kind, filters: tuple[EntityRef, ...], chain: ResultList | None) -> ResultList:
        """The entities of `kind` linked to every filter and to any entity of `chain`.

        >>> fire, blaze = repo.ref(Kind.TYPE, "fire"), repo.ref(Kind.ABILITY, "blaze")
        >>> [r.name for r in relations._list(Kind.POKEMON, (fire, blaze), None).refs]
        ['charmander', 'charmeleon', 'charizard']
        """
        refs = {e.ref for e in self.repo.by_kind[kind].values()}
        for f in filters:
            refs &= set(self.repo.linked(f, kind))
        if chain is not None:
            previous = set(chain.refs)
            refs = {r for r in refs if previous & set(self.repo.linked(r, chain.kind))}
        return ResultList(kind, filters, chain, sorted(refs))  # by number: Pokédex, move, ability, type number
