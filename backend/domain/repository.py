"""In-memory, read-only access to the Pokédex data. Indexes are built once at startup.

The repository doesn't know where the data comes from: callers pass it already read,
e.g. `Repository(read_json(path))` (see sources.py).
"""

from collections.abc import Mapping
from typing import Any

from domain.records import TYPE_IDS, Ability, Entity, EntityRef, Kind, Move, Pokemon, Type

LINKS = {(Kind.POKEMON, Kind.TYPE), (Kind.POKEMON, Kind.ABILITY), (Kind.POKEMON, Kind.MOVE), (Kind.MOVE, Kind.TYPE)}
"""The links in the data: a Pokémon is of types, has abilities, learns moves; a move is of a type. Each also reads
the other way round (a type's Pokémon). Nothing else is linked: no ability to move, no Pokémon to Pokémon."""


def can_link(a: Kind, b: Kind) -> bool:
    """Whether entities of kind `a` can be linked to entities of kind `b`.

    >>> can_link(Kind.TYPE, Kind.MOVE), can_link(Kind.ABILITY, Kind.MOVE)
    (True, False)
    """
    return (a, b) in LINKS or (b, a) in LINKS


class Repository:
    """Read-only lookups over the dataset, with the links between entities built once.

    >>> repo.pokemon["pikachu"].types
    ['electric']
    """

    def __init__(self, raw: dict[str, Any]):
        """Read the raw dataset into records indexed by name and by id, and build the links.

        >>> repo = Repository(read_json(DATA_DIR / "pokedex.json"))
        >>> len(repo.pokemon)
        151
        """
        self.pokemon: dict[str, Pokemon] = {p.name: p for p in map(Pokemon.from_json, raw["pokemon"])}
        self.moves: dict[str, Move] = {m.name: m for m in map(Move.from_json, raw["moves"])}
        self.abilities: dict[str, Ability] = {a.name: a for a in map(Ability.from_json, raw["abilities"])}
        # Types have no record in the dataset (only the names used by Pokémon and moves), so a type's record only
        # holds its name and PokeAPI's number.
        names = {t for p in self.pokemon.values() for t in p.types} | {m.type for m in self.moves.values()}
        types = {t: Type(TYPE_IDS[t], t) for t in sorted(names, key=TYPE_IDS.__getitem__)}
        # Every entity by kind and name (how the API and the queries name them), and by kind and id (its identity).
        self.by_kind: dict[Kind, Mapping[str, Entity]] = {  # Mapping: read-only, so a dict of Pokémon fits
            Kind.POKEMON: self.pokemon, Kind.MOVE: self.moves, Kind.ABILITY: self.abilities, Kind.TYPE: types,
        }
        self.by_id: dict[Kind, dict[int, Entity]] = {k: {e.id: e for e in d.values()} for k, d in self.by_kind.items()}
        # The links, both ways, as refs, read once from the Pokémon (types, abilities, moves) and the moves (type).
        # Lists are in Pokédex order, as the Pokémon come; a Pokémon's moves and abilities in its record's order.
        self._links: dict[tuple[EntityRef, Kind], list[EntityRef]] = {}
        for p in self.pokemon.values():
            for other in ([types[t] for t in p.types] + [self.abilities[a] for a in p.abilities]
                          + [self.moves[m] for m in p.moves]):
                self._link(p.ref, other.ref)
        for m in self.moves.values():
            self._link(m.ref, types[m.type].ref)

    def _link(self, a: EntityRef, b: EntityRef) -> None:
        """Record that `a` and `b` are linked, both ways."""
        self._links.setdefault((a, b.kind), []).append(b)
        self._links.setdefault((b, a.kind), []).append(a)

    def ref(self, kind: Kind, name: str) -> EntityRef:
        """The identity of the entity of `kind` named `name` (a name from the API, a URL or a test). KeyError if none.

        >>> repo.ref(Kind.POKEMON, "pikachu")
        EntityRef(kind=<Kind.POKEMON: 'pokemon'>, id=25, name='pikachu')
        """
        return self.by_kind[kind][name].ref

    def get(self, ref: EntityRef) -> Entity:
        """The record of an entity, by its identity.

        >>> repo.get(repo.ref(Kind.MOVE, "surf")).power
        90
        """
        return self.by_id[ref.kind][ref.id]

    def linked(self, ref: EntityRef, kind: Kind) -> tuple[EntityRef, ...]:
        """The entities of `kind` linked to `ref`: a type's Pokémon or moves, a Pokémon's abilities, a move's learners…
        Pokémon in Pokédex order. Empty when the two kinds aren't linked.

        >>> [r.name for r in repo.linked(repo.ref(Kind.POKEMON, "charizard"), Kind.ABILITY)]
        ['blaze', 'solar-power']
        >>> [r.name for r in repo.linked(repo.ref(Kind.MOVE, "spore"), Kind.POKEMON)]
        ['paras', 'parasect']
        >>> repo.linked(repo.ref(Kind.ABILITY, "blaze"), Kind.MOVE)
        ()
        """
        return tuple(self._links.get((ref, kind), ()))

    def all_refs(self) -> list[EntityRef]:
        """Every entity of every kind, in dataset order. Used to build the resolver's name index (the resolver
        ranks its candidates itself, so this order doesn't matter).

        >>> repo.all_refs()[0]
        EntityRef(kind=<Kind.POKEMON: 'pokemon'>, id=1, name='bulbasaur')
        """
        return [e.ref for kind in Kind for e in self.by_kind[kind].values()]

    def evolution_family(self, ref: EntityRef) -> list[EntityRef]:
        """All Pokémon sharing a Pokémon's evolution chain, in Pokédex order. Evolution methods are not in the data.

        >>> [r.name for r in repo.evolution_family(repo.ref(Kind.POKEMON, "ivysaur"))]
        ['bulbasaur', 'ivysaur', 'venusaur']
        """
        chain = self.pokemon[ref.name].evolution_chain_id
        return [p.ref for p in self.pokemon.values() if p.evolution_chain_id == chain]
