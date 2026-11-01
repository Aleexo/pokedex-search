"""Coverage moves: a Pokémon's moves of other types that get past its walls. Design and choices:
docs/MOVE_COVERAGE.md.

- Walls: the types that resist ALL of the Pokémon's own types (each hits them x0.5 or less, immunity
  included), among the 18 types of the chart. Some Pokémon have none (Geodude, Rock / Ground).
- Candidate moves: damaging (a power value), of other types than its own (no STAB), hitting at least one
  wall x2 or x1 (not resisted).
- Ranked: first the moves hitting walls x2, by how many; then those hitting walls only x1, by how many. Ties by
  estimated damage (power x accuracy x the stat the move uses: Attack if physical, Sp. Atk if special), then name.
"""

from dataclasses import dataclass

from coverage.type_chart import TypeChart
from domain.records import DamageClass, Move, Pokemon
from domain.repository import EntityRef, Kind, Repository

MAX_MOVES = 5
SUPER_EFFECTIVE = 2
NEUTRAL = 1
RESISTED = 0.5  # a type resists a move type at x0.5 or less (x0: immune)


@dataclass(frozen=True)
class CoverageMove:
    """One move as seen by this Pokémon: its stats, the stat it uses, and its multiplier on each wall.

    >>> m = advisor.suggest("charizard").moves[0]
    >>> m.ref.name, m.type, m.power, m.accuracy, m.pp, m.damage_class.value, m.stat, m.multipliers, m.hits, m.neutral
    ('earthquake', 'ground', 100, 100, 10, 'physical', 84, {'rock': 2}, 1, 0)
    """

    ref: EntityRef
    """The move."""
    type: str
    """Its type, never one of the Pokémon's own."""
    power: int
    """Base power."""
    accuracy: int | None
    """In %; None = never misses."""
    pp: int
    """Power points: how many times it can be used."""
    damage_class: DamageClass
    """Physical or special: only damaging moves are suggested."""
    stat: int
    """The Pokémon's stat this move uses: Attack (physical) or Sp. Atk (special)."""
    damage: float
    """Estimated damage for this Pokémon: power x accuracy x stat (breaks ties; not displayed)."""
    multipliers: dict[str, float]
    """Its multiplier on each of the Pokémon's walls."""
    hits: int
    """How many of those walls it hits x2: ranks it first."""
    neutral: int
    """How many of those walls it hits x1: ranks the moves that hit none x2."""


@dataclass(frozen=True)
class CoverageReport:
    """The answer for one Pokémon: its walls, its coverage moves, and notes when the list is empty.

    >>> advisor.suggest("metapod").notes
    ['This Pokémon learns no damaging move.']
    """

    pokemon: str
    """The Pokémon asked about."""
    walls: list[str]
    """The types resisting all of its own types (x0.5 or less), in alphabetical order; may be empty."""
    moves: list[CoverageMove]
    """Up to 5 moves of other types: those hitting its walls x2 first, then x1; see `_rank`."""
    notes: list[str]
    """Explain an empty list."""


class CoverageAdvisor:
    """Suggests a Pokémon's coverage moves: those of other types that get past its walls.

    >>> [(m.ref.name, m.hits, m.neutral) for m in advisor.suggest("snorlax").moves][:2]
    [('earthquake', 2, 1), ('submission', 2, 0)]
    """

    def __init__(self, repo: Repository, chart: TypeChart):
        """Keep the data and the type chart.

        >>> CoverageAdvisor(repo, chart).suggest("charizard").walls
        ['rock']
        """
        self.repo = repo
        self.chart = chart

    def suggest(self, name: str, limit: int = MAX_MOVES) -> CoverageReport:
        """The coverage moves of one Pokémon (KeyError if unknown).

        >>> r = advisor.suggest("pikachu")
        >>> r.walls, [(m.ref.name, m.hits, m.neutral) for m in r.moves][:2]
        (['dragon', 'electric', 'grass', 'ground'], [('surf', 1, 1), ('skull-bash', 0, 4)])
        """
        pokemon = self.repo.pokemon[name]
        walls = self.walls(pokemon)
        damaging = [self.repo.moves[m] for m in pokemon.moves if self.repo.moves[m].power is not None]
        others = [m for m in damaging if m.type not in pokemon.types]  # coverage: no STAB
        moves = [self._build(pokemon, m, walls) for m in others] if walls else []
        moves = sorted((m for m in moves if m.hits or m.neutral), key=_rank)  # not resisted by every wall

        notes = []
        if not walls:
            notes.append("No type resists all of its types: its own-type moves leave nothing to cover.")
        elif not damaging:
            notes.append("This Pokémon learns no damaging move.")
        elif not others:
            notes.append("It learns no damaging move of another type than its own.")
        elif not moves:
            notes.append("All its walls resist every damaging move of another type it learns.")
        return CoverageReport(name, walls, moves[:limit], notes)

    def walls(self, pokemon: Pokemon) -> list[str]:
        """The types resisting all of this Pokémon's own types: each of its types hits them x0.5 or less (x0 too).

        >>> advisor.walls(repo.pokemon["pikachu"])  # Electric: x0.5 on Dragon, Electric, Grass; x0 on Ground
        ['dragon', 'electric', 'grass', 'ground']
        >>> advisor.walls(repo.pokemon["charizard"]), advisor.walls(repo.pokemon["geodude"])
        (['rock'], [])
        """
        return [t for t in self.chart.chart if all(self.chart.multiplier(own, t) <= RESISTED for own in pokemon.types)]

    def _build(self, pokemon: Pokemon, move: Move, walls: list[str]) -> CoverageMove:
        """A move as seen by this Pokémon: its stat, estimated damage, and multiplier on each wall.
        Estimated damage: power x accuracy (a move with no accuracy value never misses: 100 %) x the stat used.

        >>> m = advisor._build(repo.pokemon["geodude"], repo.moves["fire-blast"], ["grass", "water"])
        >>> m.stat, m.damage, m.multipliers, m.hits, m.neutral  # special: Geodude's Sp. Atk 30; 110 x 85 % x 30
        (30, 2805.0, {'grass': 2, 'water': 0.5}, 1, 0)
        """
        assert move.power is not None, move.name  # only damaging moves are built
        stat = _stat(pokemon, move)
        multipliers = {w: self.chart.multiplier(move.type, w) for w in walls}
        return CoverageMove(move.ref, move.type, move.power, move.accuracy, move.pp,
                            move.damage_class, stat, move.power * (move.accuracy or 100) / 100 * stat, multipliers,
                            sum(1 for x in multipliers.values() if x >= SUPER_EFFECTIVE),
                            sum(1 for x in multipliers.values() if x == NEUTRAL))


def _rank(m: CoverageMove) -> tuple:
    """Sort key: the moves hitting walls x2 first, by how many; then those hitting walls only x1, by how many.
    Ties: the highest estimated damage, then the name.

    >>> [m.ref.name for m in sorted(advisor.suggest("pinsir").moves, key=_rank)][:2]  # Submission: x2 on 1 wall
    ['submission', 'double-edge']
    """
    if m.hits:
        return (0, -m.hits, -m.damage, m.ref.name)
    return (1, -m.neutral, -m.damage, m.ref.name)


def _stat(pokemon: Pokemon, move: Move) -> int:
    """The Pokémon's stat a move uses: Attack for a physical move, Sp. Atk for a special one.

    >>> _stat(repo.pokemon["geodude"], repo.moves["submission"]), _stat(repo.pokemon["geodude"], repo.moves["fire-blast"])
    (80, 30)
    """
    return pokemon.stats.attack if move.damage_class is DamageClass.PHYSICAL else pokemon.stats.special_attack

