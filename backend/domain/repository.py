"""In-memory, read-only access to the Pokédex data. Indexes are built once at startup.

The repository doesn't know where the data comes from: callers pass it already read,
e.g. `Repository(read_json(path))` (see sources.py).
"""

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from domain.records import Ability, Move, Pokemon, Record, Type


class Kind(StrEnum):
    """StrEnum: members compare equal to, and serialise as, their string value (JSON, URLs, YAML).

    >>> Kind("move") is Kind.MOVE
    True
    """

    POKEMON = "pokemon"
    MOVE = "move"
    ABILITY = "ability"
    TYPE = "type"


@dataclass(frozen=True, order=True)
class EntityRef:
    """Identity of an entity. Names are only unique within a kind: 'psychic' is a type and a move.

    >>> EntityRef(Kind.MOVE, "psychic") == EntityRef(Kind.TYPE, "psychic")
    False
    """

    kind: Kind
    """What it is: Pokémon, move, ability or type."""
    name: str
    """Its dataset name, unique within the kind: "thunder-wave", "mr-mime"."""


class Repository:
    """Read-only lookups over the dataset, with reverse indexes built once.

    >>> repo.pokemon["pikachu"].types
    ['electric']
    """

    def __init__(self, raw: dict[str, Any]):
        """Read the raw dataset into records indexed by name, and build the type indexes.

        >>> repo = Repository(read_json(DATA_DIR / "pokedex.json"))
        >>> len(repo.pokemon)
        151
        """
        self.pokemon = {p.name: p for p in map(Pokemon.from_json, raw["pokemon"])}
        self.moves = {m.name: m for m in map(Move.from_json, raw["moves"])}
        self.abilities = {a.name: a for a in map(Ability.from_json, raw["abilities"])}

        self.pokemon_by_type: dict[str, list[str]] = defaultdict(list)
        for p in self.pokemon.values():
            for t in p.types:
                self.pokemon_by_type[t].append(p.name)
        self.moves_by_type: dict[str, list[str]] = defaultdict(list)
        for m in self.moves.values():
            self.moves_by_type[m.type].append(m.name)
        # Every entity by kind and name. Types have no record in the dataset (only names used by Pokémon
        # and moves), so a type's record only holds its name.
        types = set(self.pokemon_by_type) | set(self.moves_by_type)
        self.by_kind: dict[Kind, Mapping[str, Record]] = {  # Mapping: read-only, so a dict of Pokémon fits
            Kind.POKEMON: self.pokemon, Kind.MOVE: self.moves, Kind.ABILITY: self.abilities,
            Kind.TYPE: {t: Type(t) for t in types},
        }

    def exists(self, ref: EntityRef) -> bool:
        """Whether the entity is in the dataset.

        >>> repo.exists(EntityRef(Kind.POKEMON, "agumon")), repo.exists(EntityRef(Kind.TYPE, "fire"))
        (False, True)
        """
        return ref.name in self.by_kind[ref.kind]

    def all_refs(self) -> list[EntityRef]:
        """Every entity of every kind, in dataset order. Used to build the resolver's name index (the resolver
        ranks its candidates itself, so this order doesn't matter).

        >>> repo.all_refs()[0]
        EntityRef(kind=<Kind.POKEMON: 'pokemon'>, name='bulbasaur')
        """
        return [EntityRef(kind, name) for kind in Kind for name in self.by_kind[kind]]

    def evolution_family(self, name: str) -> list[str]:
        """All Pokémon sharing an evolution chain, in dataset order (the file lists Pokémon by Pokédex number).
        Evolution methods are not in the data.

        >>> repo.evolution_family("ivysaur")
        ['bulbasaur', 'ivysaur', 'venusaur']
        """
        chain = self.pokemon[name].evolution_chain_id
        return [n for n, p in self.pokemon.items() if p.evolution_chain_id == chain]

    def pokemon_with(self, ref: EntityRef) -> list[str]:
        """Pokémon linked to a move (learns it), ability (has it) or type (is that type).

        >>> repo.pokemon_with(EntityRef(Kind.MOVE, "spore"))
        ['paras', 'parasect']
        """
        if ref.kind is Kind.MOVE:
            return list(self.moves[ref.name].learned_by_pokemon)
        if ref.kind is Kind.ABILITY:
            return list(self.abilities[ref.name].pokemon)
        if ref.kind is Kind.TYPE:
            return list(self.pokemon_by_type.get(ref.name, []))
        return []
