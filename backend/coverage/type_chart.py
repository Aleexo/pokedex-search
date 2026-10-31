"""The type chart: damage multipliers between types, read from the committed data/type_chart.json."""

from pathlib import Path

from domain.sources import DATA_DIR, read_json


class TypeChart:
    """Damage multipliers dealt by an attacking type to defending types (x1 when not listed).

    >>> chart.multiplier("electric", "ground"), chart.multiplier("fire", "normal")
    (0, 1)
    """

    def __init__(self, chart: dict[str, dict[str, float]]):
        """Wrap a chart {attacking type: {defending type: multiplier}}, with every type as a key (alphabetical).

        >>> TypeChart({"fire": {"grass": 2}}).multiplier("fire", "grass")
        2
        """
        self.chart = chart

    @classmethod
    def from_data(cls, data_dir: Path = DATA_DIR) -> "TypeChart":
        """Load the committed chart (fetched once from PokeAPI by scripts/fetch_type_chart.py).

        >>> len(TypeChart.from_data().chart)
        18
        """
        return cls(read_json(data_dir / "type_chart.json")["chart"])

    def multiplier(self, attack: str, defend: str) -> float:
        """Multiplier of one attacking type against one defending type.

        >>> chart.multiplier("water", "fire")
        2
        """
        return self.chart[attack].get(defend, 1)
