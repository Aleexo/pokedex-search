from domain.records import DamageClass, Type
from domain.repository import EntityRef, Kind, Repository
from domain.sources import DATA_DIR, read_json


def test_repository_works_with_any_data():
    """The repository only needs data, not a file: a dict built in memory works."""
    stats = {"hp": 1, "attack": 1, "defense": 1, "special-attack": 1, "special-defense": 1, "speed": 1}
    repo = Repository({
        "metadata": {},
        "pokemon": [{"id": 1, "name": "testmon", "types": ["fire"], "stats": stats, "abilities": [], "moves": ["ember"],
                     "height_decimetres": 10, "weight_hectograms": 100, "images": {"sprite": ""},
                     "species": {"genus": "", "description": "", "evolution_chain_id": 1}}],
        "moves": [{"id": 1, "name": "ember", "type": "fire", "damage_class": "special", "power": 40, "accuracy": 100,
                   "pp": 25, "effect_chance": 10, "short_effect": "", "learned_by_pokemon": ["testmon"]}],
        "abilities": [],
    })
    assert repo.pokemon_with(EntityRef(Kind.MOVE, "ember")) == ["testmon"]
    assert repo.exists(EntityRef(Kind.TYPE, "fire"))
    assert (repo.pokemon["testmon"].height_m, repo.pokemon["testmon"].weight_kg) == (1.0, 10.0)  # m and kg


def test_read_json_reads_the_bundled_dataset():
    """read_json reads the real dataset (151 Pokémon)."""
    assert len(Repository(read_json(DATA_DIR / "pokedex.json")).pokemon) == 151


def test_every_move_has_a_known_damage_class(engine):
    """The damage class enum covers the data: every move is physical, special or status."""
    assert {m.damage_class for m in engine.repo.moves.values()} == set(DamageClass)


def test_by_kind_holds_every_kind_types_included(engine):
    """One dict per kind; a type has no record in the data, so its record only holds its name."""
    repo = engine.repo
    assert [len(repo.by_kind[k]) for k in Kind] == [151, 164, 114, 18]
    assert repo.by_kind[Kind.TYPE]["fire"] == Type("fire")
    assert repo.by_kind[Kind.MOVE]["surf"] is repo.moves["surf"]
