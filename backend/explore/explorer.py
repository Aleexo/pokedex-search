"""Exploration: rank Pokémon or moves on one numeric field: the rows with the highest (or lowest) value.

The field decides the subject: a Pokémon field (stats, height, weight) ranks Pokémon, a move field (power,
accuracy, PP, effect chance) ranks moves. Each is ranked alone (one row per Pokémon or move) or by type (one
row per type, the field averaged over its Pokémon or moves; a Pokémon with two types counts in both). A move
without a value for the chosen field (a status move has no power) is left out.

The type filter keeps Pokémon with any of the chosen types, or moves of one of those types.
"""

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from domain.records import Move, Pokemon
from domain.repository import EntityRef, Kind, Repository

MAX_ROWS = 8


class Subject(StrEnum):
    """What Explore ranks: Pokémon or moves.

    >>> Subject.MOVE.kind, Subject.POKEMON.noun
    (<Kind.MOVE: 'move'>, 'Pokémon')
    """

    POKEMON = "pokemon"
    MOVE = "move"

    @property
    def kind(self) -> Kind:
        """Kind of entity a row is when ranked alone, so it can be opened in the details panel.

        >>> Subject.POKEMON.kind
        <Kind.POKEMON: 'pokemon'>
        """
        return Kind(self.value)

    @property
    def noun(self) -> str:
        """Plural shown in "44 of 151 Pokémon".

        >>> Subject.MOVE.noun
        'moves'
        """
        return "moves" if self is Subject.MOVE else "Pokémon"


class Number(StrEnum):
    """A numeric field: a Pokémon stat or measure (m, kg), or a move field.

    >>> Number("speed").label, Number.POWER.subject
    ('Speed', <Subject.MOVE: 'move'>)
    """

    # Pokémon fields
    HP = "hp"
    ATTACK = "attack"
    DEFENSE = "defense"
    SPECIAL_ATTACK = "special-attack"
    SPECIAL_DEFENSE = "special-defense"
    SPEED = "speed"
    HEIGHT = "height"
    WEIGHT = "weight"
    # Move fields
    POWER = "power"
    ACCURACY = "accuracy"
    PP = "pp"
    EFFECT_CHANCE = "effect-chance"

    @property
    def label(self) -> str:
        """Name shown in the menus and on the axes.

        >>> Number.WEIGHT.label
        'Weight (kg)'
        """
        return _NUMBER_LABELS[self]

    @property
    def subject(self) -> Subject:
        """What this field ranks: moves for a move field, Pokémon otherwise.

        >>> Number.PP.subject, Number.HP.subject
        (<Subject.MOVE: 'move'>, <Subject.POKEMON: 'pokemon'>)
        """
        return Subject.MOVE if self in _MOVE_VALUES else Subject.POKEMON


_NUMBER_LABELS = {
    Number.HP: "HP", Number.ATTACK: "Attack", Number.DEFENSE: "Defense",
    Number.SPECIAL_ATTACK: "Sp. Atk", Number.SPECIAL_DEFENSE: "Sp. Def", Number.SPEED: "Speed",
    Number.HEIGHT: "Height (m)", Number.WEIGHT: "Weight (kg)",
    Number.POWER: "Power", Number.ACCURACY: "Accuracy (%)", Number.PP: "PP",
    Number.EFFECT_CHANCE: "Effect chance (%)",
}
# How each field is read from a Pokémon (always a value), or from a move (None when it has none).
_POKEMON_VALUES: dict[Number, Callable[[Pokemon], float]] = {
    Number.HP: lambda p: p.stats.hp, Number.ATTACK: lambda p: p.stats.attack,
    Number.DEFENSE: lambda p: p.stats.defense, Number.SPECIAL_ATTACK: lambda p: p.stats.special_attack,
    Number.SPECIAL_DEFENSE: lambda p: p.stats.special_defense, Number.SPEED: lambda p: p.stats.speed,
    Number.HEIGHT: lambda p: p.height_m, Number.WEIGHT: lambda p: p.weight_kg,
}
def _accuracy(move: Move) -> float | None:
    """A move's accuracy in %. A damaging move without one never misses (Swift): 100. A status move without one
    (Swords Dance, Splash…) acts on the user or the field, so accuracy doesn't apply: None, left out.

    >>> _accuracy(repo.moves["surf"]), _accuracy(repo.moves["swift"]), _accuracy(repo.moves["swords-dance"])
    (100, 100, None)
    """
    if move.accuracy is None and move.power is not None:
        return 100
    return move.accuracy


_MOVE_VALUES: dict[Number, Callable[[Move], float | None]] = {
    Number.POWER: lambda m: m.power, Number.ACCURACY: _accuracy, Number.PP: lambda m: m.pp,
    Number.EFFECT_CHANCE: lambda m: m.effect_chance,
}


class Order(StrEnum):
    """Which end of the ranking to show.

    >>> Order("bottom") is Order.BOTTOM
    True
    """

    TOP = "top"
    BOTTOM = "bottom"


@dataclass(frozen=True)
class Row:
    """One bar or table row: an entity, its value, and how many Pokémon (or moves) it averages or can learn it.

    >>> explorer.ranked(Number.SPEED)[0]
    Row(ref=EntityRef(kind=<Kind.POKEMON: 'pokemon'>, name='electrode'), x=150, count=1)
    """

    ref: EntityRef
    """What the row is: a Pokémon, a move or a type."""
    x: float
    """The value ranked on (an average for a type)."""
    count: int
    """Pokémon (or moves) averaged; for a move row, Pokémon that can learn it."""


class Explorer:
    """Ranks the 151 Pokémon or the 164 moves, alone or by type, on one numeric field.

    The type filter (`types`) keeps Pokémon with any of those types, or moves of one of them; empty = all.

    >>> [r.ref.name for r in explorer.ranked(Number.SPEED, by_type=True)][:3]
    ['electric', 'ghost', 'flying']
    >>> [r.ref.name for r in explorer.ranked(Number.POWER)][:3]
    ['explosion', 'self-destruct', 'hyper-beam']
    """

    def __init__(self, repo: Repository):
        """Keep the repository; rows are computed per request (151 Pokémon, well under a millisecond).

        >>> Explorer(repo).ranked(Number.HP)[0].ref.name
        'chansey'
        """
        self.repo = repo

    def pokemon(self, types: frozenset[str] = frozenset()) -> list[Pokemon]:
        """The Pokémon with any of `types` (all if empty).

        >>> [p.name for p in explorer.pokemon(frozenset({"dragon"}))]
        ['dratini', 'dragonair', 'dragonite']
        """
        return [p for p in self.repo.pokemon.values() if not types or types & set(p.types)]

    def moves(self, types: frozenset[str] = frozenset()) -> list[Move]:
        """The moves of one of `types` (all if empty).

        >>> [m.name for m in explorer.moves(frozenset({"dragon"}))]
        ['dragon-rage']
        """
        return [m for m in self.repo.moves.values() if not types or m.type in types]

    def ranked(self, x: Number, by_type: bool = False, order: Order = Order.TOP,
               types: frozenset[str] = frozenset()) -> list[Row]:
        """Every row, best first (the API shows the first MAX_ROWS). Ties are broken by name so the result is stable.

        >>> [(r.ref.name, r.x) for r in explorer.ranked(Number.SPEED)][1:4]
        [('aerodactyl', 130), ('jolteon', 130), ('mewtwo', 130)]
        """
        return sorted(self.rows(x, by_type, types), key=lambda r: (-r.x if order is Order.TOP else r.x, r.ref))

    def rows(self, x: Number, by_type: bool = False, types: frozenset[str] = frozenset()) -> list[Row]:
        """Every row, unranked: one per Pokémon or move with a value for `x`, or one per type averaging them.

        Raises ValueError if a type filter is combined with grouping by type: one or the other.

        >>> next(r for r in explorer.rows(Number.SPEED, by_type=True) if r.ref.name == "dragon")
        Row(ref=EntityRef(kind=<Kind.TYPE: 'type'>, name='dragon'), x=66.7, count=3)
        >>> next(r for r in explorer.rows(Number.POWER) if r.ref.name == "surf")  # count: Pokémon learning it
        Row(ref=EntityRef(kind=<Kind.MOVE: 'move'>, name='surf'), x=90, count=42)
        """
        if by_type and types:
            raise ValueError("Filter by type or group by type, not both")
        # (name, its types, value, count) for each Pokémon or move with a value
        items: list[tuple[str, list[str], float, int]]
        if x.subject is Subject.MOVE:
            move_value = _MOVE_VALUES[x]
            items = [(m.name, [m.type], v, len(m.learned_by_pokemon))
                     for m in self.moves(types) if (v := move_value(m)) is not None]  # a status move has no power
        else:
            pokemon_value = _POKEMON_VALUES[x]
            items = [(p.name, p.types, pokemon_value(p), 1) for p in self.pokemon(types)]
        if not by_type:
            return [Row(EntityRef(x.subject.kind, name), v, count) for name, _, v, count in items]
        groups: dict[str, list[float]] = defaultdict(list)
        for _, own, v, _ in items:
            for t in own:
                groups[t].append(v)
        return [Row(EntityRef(Kind.TYPE, t), _mean(values), len(values)) for t, values in groups.items()]


def tied_beyond(ranked: list[Row], limit: int = MAX_ROWS) -> int:
    """How many rows past the cut have the same value as the last row shown (left out only by name order).

    >>> tied_beyond(explorer.ranked(Number.SPEED))  # 8th is Starmie (115); the 9th, Dodrio, has 110
    0
    """
    if len(ranked) <= limit:
        return 0
    last = ranked[limit - 1].x
    return sum(1 for r in ranked[limit:] if r.x == last)


def _mean(values: list[float]) -> float:
    """Average, rounded to 1 decimal; a single value is returned as is.

    >>> _mean([45, 60]), _mean([150])
    (52.5, 150)
    """
    return values[0] if len(values) == 1 else round(sum(values) / len(values), 1)
