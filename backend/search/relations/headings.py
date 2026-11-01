"""The wording of the relation search's lists, built at the end, when the lists are sent: "Pokémon of type Fire, with
Blaze". The search itself only returns what each list is (its kind, its filters, the list it follows).
"""

from domain.repository import EntityRef, Kind
from search.relations.relations import ResultList

PLURAL = {Kind.POKEMON: "Pokémon", Kind.MOVE: "moves", Kind.ABILITY: "abilities", Kind.TYPE: "types"}
FILTER_ORDER = [Kind.TYPE, Kind.ABILITY, Kind.MOVE, Kind.POKEMON]  # the order of the phrases in a heading


def heading(result: ResultList) -> list[str | EntityRef]:
    """The heading of a list: text and the entities it names (shown as chips), capitalised.

    >>> fire, blaze = repo.ref(Kind.TYPE, "fire"), repo.ref(Kind.ABILITY, "blaze")
    >>> heading(ResultList(Kind.POKEMON, (fire, blaze), None, []))
    ['Pokémon of type ', EntityRef(kind=<Kind.TYPE: 'type'>, id=10, name='fire'), ' with ', EntityRef(kind=<Kind.ABILITY: 'ability'>, id=66, name='blaze')]
    """
    parts = _parts(result)
    if isinstance(parts[0], str):
        parts[0] = parts[0][:1].upper() + parts[0][1:]
    return parts


def title(result: ResultList) -> str:
    """The heading as plain text (the entities by their display name, as `display_name`): for tests and logs.

    >>> blaze_pokemon = ResultList(Kind.POKEMON, (repo.ref(Kind.ABILITY, "blaze"),), None, [])
    >>> title(ResultList(Kind.MOVE, (), blaze_pokemon, []))  # a chain: the moves of the Pokémon with Blaze
    'Moves learned by Pokémon with Blaze'
    """
    return "".join(p if isinstance(p, str) else p.name.replace("-", " ").title() for p in heading(result))


def _parts(result: ResultList) -> list[str | EntityRef]:
    """The heading, lowercase, so that it can be nested in the next list's (`moves learned by Pokémon with Blaze`).

    >>> _parts(ResultList(Kind.MOVE, (repo.ref(Kind.TYPE, "poison"),), None, []))
    ['moves of type ', EntityRef(kind=<Kind.TYPE: 'type'>, id=4, name='poison')]
    """
    filters = sorted(result.filters, key=lambda f: FILTER_ORDER.index(f.kind))
    phrases: list[list[str | EntityRef]] = [[_phrase(result.kind, f.kind), f] for f in filters]
    if result.chain is not None:
        phrases.append([_phrase(result.kind, result.chain.kind), *_parts(result.chain)])
    parts: list[str | EntityRef] = [PLURAL[result.kind] if phrases else "all " + PLURAL[result.kind]]
    # A type reads like an adjective: "of type Fire" is followed directly by the next phrase (Pokémon of type Fire
    # with Blaze); the other phrases are joined with commas and "and".
    if filters and filters[0].kind is Kind.TYPE:
        parts += [" ", *phrases.pop(0)]
    for i, phrase in enumerate(phrases):
        parts += [" " if i == 0 else " and " if i == len(phrases) - 1 else ", ", *phrase]
    return _merge(parts)


def _phrase(kind: Kind, filter_kind: Kind) -> str:
    """How a filter of `filter_kind` reads in a heading of `kind`.

    >>> _phrase(Kind.POKEMON, Kind.MOVE), _phrase(Kind.MOVE, Kind.POKEMON), _phrase(Kind.ABILITY, Kind.POKEMON)
    ('that learn ', 'learned by ', 'of ')
    """
    if filter_kind is Kind.TYPE and kind in (Kind.POKEMON, Kind.MOVE):
        return "of type "
    if kind is Kind.POKEMON:
        return "with " if filter_kind is Kind.ABILITY else "that learn "
    if kind is Kind.MOVE:
        return "learned by "
    return "of "


def _merge(parts: list[str | EntityRef]) -> list[str | EntityRef]:
    """Join neighbouring strings, so the heading alternates text and entities.

    >>> _merge(["moves", " ", "of type ", repo.ref(Kind.TYPE, "fire")])
    ['moves of type ', EntityRef(kind=<Kind.TYPE: 'type'>, id=10, name='fire')]
    """
    merged: list[str | EntityRef] = []
    for p in parts:
        if isinstance(p, str) and merged and isinstance(merged[-1], str):
            merged[-1] += p
        else:
            merged.append(p)
    return merged
