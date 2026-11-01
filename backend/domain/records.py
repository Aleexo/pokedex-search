"""The dataset's records as typed objects: Pokémon, moves, abilities, types, all `Entity`; their `Kind` and
identity (`EntityRef`).

`from_json` is the only place that reads the JSON keys; the rest of the code uses attributes, checked by mypy.
Units are converted on loading: heights in m, weights in kg (the file has decimetres and hectograms).
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import ClassVar


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
    """Identity of an entity: its kind and its number in that kind (move 94 and type 14 are both "psychic"). The
    name is carried for display only: equality, hashing and order use kind and id.

    >>> repo.ref(Kind.MOVE, "psychic") == repo.ref(Kind.TYPE, "psychic"), repo.ref(Kind.MOVE, "psychic").id
    (False, 94)
    """

    kind: Kind
    """What it is: Pokémon, move, ability or type."""
    id: int
    """Its number within its kind: Pokédex number, move or ability number, PokeAPI's type number."""
    name: str = field(compare=False)
    """Its dataset name, for display, logs and the API: "thunder-wave", "mr-mime"."""


@dataclass(frozen=True)
class Entity:
    """What every record has: its kind, number and dataset name. Pokémon, moves, abilities and types inherit it.

    >>> repo.moves["surf"].kind, repo.moves["surf"].ref
    (<Kind.MOVE: 'move'>, EntityRef(kind=<Kind.MOVE: 'move'>, id=57, name='surf'))
    """

    kind: ClassVar[Kind]
    """Set by each subclass: Pokémon, move, ability or type."""
    id: int
    """Its number within its kind: Pokédex number, move or ability number; a type's from `TYPE_IDS`."""
    name: str
    """Its dataset name, unique within its kind: "thunder-wave", "mr-mime"."""

    @property
    def ref(self) -> EntityRef:
        """Its identity: kind and id (with its name, for display).

        >>> repo.pokemon["pikachu"].ref
        EntityRef(kind=<Kind.POKEMON: 'pokemon'>, id=25, name='pikachu')
        """
        return EntityRef(self.kind, self.id, self.name)


class DamageClass(StrEnum):
    """How a move works: with the Attack stat, with Sp. Atk, or without damage (a move's `damage_class`).

    >>> repo.moves["surf"].damage_class is DamageClass.SPECIAL
    True
    """

    PHYSICAL = "physical"  # uses Attack
    SPECIAL = "special"    # uses Sp. Atk
    STATUS = "status"      # no damage


@dataclass(frozen=True)
class Stats:
    """A Pokémon's six base stats.

    >>> repo.pokemon["pikachu"].stats.speed
    90
    """

    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int

    @staticmethod
    def from_json(raw: dict) -> "Stats":
        """Read a `stats` object of the dataset.

        >>> Stats.from_json({"hp": 1, "attack": 2, "defense": 3, "special-attack": 4, "special-defense": 5, "speed": 6}).special_attack
        4
        """
        return Stats(raw["hp"], raw["attack"], raw["defense"], raw["special-attack"], raw["special-defense"], raw["speed"])


@dataclass(frozen=True)
class Pokemon(Entity):
    """One Pokémon, with the fields the app uses.

    >>> p = repo.pokemon["bulbasaur"]
    >>> p.id, p.types, p.height_m, p.weight_kg
    (1, ['grass', 'poison'], 0.7, 6.9)
    """

    kind = Kind.POKEMON
    types: list[str]
    stats: Stats
    abilities: list[str]
    """Ability names."""
    moves: list[str]
    """Names of the moves it can learn."""
    height_m: float
    weight_kg: float
    genus: str
    """E.g. "Seed Pokémon"."""
    description: str
    evolution_chain_id: int
    """Shared by every Pokémon of one evolution family."""
    sprite: str
    """Image URL (remote)."""

    @staticmethod
    def from_json(raw: dict) -> "Pokemon":
        """Read one Pokémon of the dataset, converting units to m and kg.

        >>> Pokemon.from_json(read_json(DATA_DIR / "pokedex.json")["pokemon"][24]).name
        'pikachu'
        """
        species = raw["species"]
        return Pokemon(raw["id"], raw["name"], raw["types"], Stats.from_json(raw["stats"]), raw["abilities"],
                       raw["moves"], raw["height_decimetres"] / 10, raw["weight_hectograms"] / 10,
                       species["genus"], species["description"], species["evolution_chain_id"], raw["images"]["sprite"])


@dataclass(frozen=True)
class Move(Entity):
    """One move. A field without a value in the data is None (a status move has no power).

    >>> m = repo.moves["surf"]
    >>> m.type, m.power, m.accuracy, m.pp
    ('water', 90, 100, 15)
    """

    kind = Kind.MOVE
    type: str
    damage_class: DamageClass
    power: int | None
    accuracy: int | None
    """In %; None = never misses."""
    pp: int
    """Power points: how many times it can be used."""
    effect_chance: int | None
    """In %: chance of the move's side effect."""
    short_effect: str
    learned_by_pokemon: list[str]

    @staticmethod
    def from_json(raw: dict) -> "Move":
        """Read one move of the dataset.

        >>> Move.from_json(read_json(DATA_DIR / "pokedex.json")["moves"][0]).name
        'pound'
        """
        return Move(raw["id"], raw["name"], raw["type"], DamageClass(raw["damage_class"]), raw["power"], raw["accuracy"],
                    raw["pp"], raw["effect_chance"], raw["short_effect"], raw["learned_by_pokemon"])


@dataclass(frozen=True)
class Ability(Entity):
    """One ability.

    >>> repo.abilities["overgrow"].pokemon[:2]
    ['bulbasaur', 'ivysaur']
    """

    kind = Kind.ABILITY
    short_effect: str
    pokemon: list[str]
    """Names of the Pokémon that have it."""

    @staticmethod
    def from_json(raw: dict) -> "Ability":
        """Read one ability of the dataset.

        >>> Ability.from_json(read_json(DATA_DIR / "pokedex.json")["abilities"][0]).name
        'stench'
        """
        return Ability(raw["id"], raw["name"], raw["short_effect"], raw["pokemon"])


@dataclass(frozen=True)
class Type(Entity):
    """A type. The dataset has no type records, only the names used by Pokémon and moves.

    >>> repo.by_kind[Kind.TYPE]["fire"]
    Type(id=10, name='fire')
    """

    kind = Kind.TYPE


TYPE_IDS = {
    "normal": 1, "fighting": 2, "flying": 3, "poison": 4, "ground": 5, "rock": 6, "bug": 7, "ghost": 8, "steel": 9,
    "fire": 10, "water": 11, "grass": 12, "electric": 13, "psychic": 14, "ice": 15, "dragon": 16, "dark": 17, "fairy": 18,
}
"""The types' numbers, which pokedex.json lacks: PokeAPI's (https://pokeapi.co/api/v2/type/{name}, field `id`)."""
