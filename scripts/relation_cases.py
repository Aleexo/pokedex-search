"""Compute the expected results of the relation search's labelled cases and write backend/tests/cases/relations.yaml.

The expected lists are worked out here, independently of the code under test (backend/search/relations/): the links
are read straight from data/pokedex.json, and the rules of docs/RELATION_SEARCH.md and the headings' wording are
written again below. Only the name matching comes from the name search (`EntityResolver`), which has its own
labelled cases. To change a case, edit CASES and run:

    uv run --directory backend python ../scripts/relation_cases.py           # from pokedex-search/: write the file
    uv run --directory backend python ../scripts/relation_cases.py --check   # only compare; exit 1 if it differs
"""

import json
import sys
from itertools import product
from pathlib import Path

from rapidfuzz.distance import OSA

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from domain.records import TYPE_IDS  # noqa: E402  (the types' numbers, which the data lacks)
from domain.repository import Repository  # noqa: E402
from domain.sources import read_json  # noqa: E402
from search.names.normalize import normalize  # noqa: E402
from search.names.resolver import EntityResolver  # noqa: E402

OUTPUT = ROOT / "backend" / "tests" / "cases" / "relations.yaml"

# (section, query, comment): the cases, in the file's order.
CASES = [
    ("one_filter", "poison moves", ""),
    ("one_filter", "fire pokemon", ""),
    ("one_filter", "pikachu moves", ""),
    ("one_filter", "thunderbolt pokemon", ""),
    ("one_filter", "static pokemon", ""),
    ("one_filter", "charizard abilities", ""),
    ("one_filter", "moves pikachu", "the last kind word takes the items after it"),
    ("typos_and_ties", "posion moves", "typo: the type is closest to the full word"),
    ("typos_and_ties", "rock pokemon", "exact name wins over Rock Head, Rock Slide…"),
    ("typos_and_ties", "psychic pokemon", "type and move both exact: one list each"),
    ("typos_and_ties", "nidoran moves", "a tie on the full word: one list each"),
    ("typos_and_ties", "char pokemon", "char is Charizard (closest to the full name), so pokemon is its label"),
    ("several_kinds_all_hold", "fire pokemon ability blaze and fire blast", ""),
    ("several_kinds_all_hold", "pokemon fire blaze fire blast", "fire blaze is Fire and Blaze, not a misspelt Fire Blast"),
    ("several_kinds_all_hold", "pikachu electric moves", ""),
    ("several_kinds_all_hold", "charizard fire moves", ""),
    ("several_kinds_all_hold", "electric pokemon static", ""),
    ("several_kinds_all_hold", "water pokemon ice beam", ""),
    ("several_kinds_all_hold", "snorlax moves psychic", "the type, as the move can't filter moves"),
    ("same_kind_one_list_each", "blaze overgrow pokemon", ""),
    ("same_kind_one_list_each", "fire water pokemon", "no Fire and Water Pokémon: or, never and"),
    ("same_kind_one_list_each", "pikachu raichu moves", ""),
    ("labels", "fire type pokemon", "type is a label"),
    ("labels", "thunderbolt move pokemon", "move is a label"),
    ("labels", "mirror move pokemon", "the full name first"),
    ("chains", "overgrow pokemon types", ""),
    ("chains", "dragon pokemon types", ""),
    ("chains", "pikachu moves types", ""),
    ("chains", "electric pokemon abilities", ""),
    ("chains", "blaze pokemon moves", ""),
    ("chains", "fire moves pokemon", ""),
    ("chains", "blaze pokemon fire moves", "Fire goes to the next kind word"),
    ("chains", "pikachu moves electric pokemon", "Electric goes to the next kind word"),
    ("chains", "psychic pokemon fire moves", "two readings of psychic"),
    ("chains", "pikachu moves pokemon", "large but correct"),
    ("chains", "electric pokemon static moves", "Static can only filter the Pokémon, so it goes back to them"),
    ("chains", "pikachu moves thunder pokemon", "moves is no label: Pikachu, before it, can be filtered by it"),
    ("kind_words_matched_like_names", "fire poke", "the start of pokemon"),
    ("kind_words_matched_like_names", "pikachu abilities", "a plural: up to 3 typos from 7 letters"),
    ("kind_words_matched_like_names", "agility pokemon", "Agility is a move: an exact name wins over a kind word (2 typos from ability)"),
    ("kind_words_matched_like_names", "charizard abilites", "a missing letter"),
    ("kind_words_matched_like_names", "pikachu more", "more is one typo from move (limitation)"),
    ("kind_word_alone", "pokemon", ""),
    ("kind_word_alone", "moves", ""),
    ("nothing", "grass move fire", "Fire comes after a group that already has a type"),
    ("nothing", "fire pokemon with blaze", "with -> Withdraw: no Fire Pokémon with Blaze learns it (limitation)"),
    ("no_kind_word_unchanged", "pikachu pokemon", "pokemon is a label: no kind word left"),
    ("no_kind_word_unchanged", "pikachu thunderbolt", ""),
    ("no_kind_word_unchanged", "fire blaze fire blast", ""),
]

KINDS = ["pokemon", "move", "ability", "type"]
PLURAL = {"pokemon": "Pokémon", "move": "moves", "ability": "abilities", "type": "types"}
LINKABLE = {("pokemon", "type"), ("pokemon", "ability"), ("pokemon", "move"), ("move", "type")}
LINKABLE |= {(b, a) for a, b in LINKABLE}

# The data, read directly: entities as (kind, name), their numbers, and the links both ways.
DATA = json.loads((ROOT / "data" / "pokedex.json").read_text(encoding="utf-8"))
NUMBER = {("pokemon", p["name"]): p["id"] for p in DATA["pokemon"]}
NUMBER |= {("move", m["name"]): m["id"] for m in DATA["moves"]}
NUMBER |= {("ability", a["name"]): a["id"] for a in DATA["abilities"]}
NUMBER |= {("type", t): n for t, n in TYPE_IDS.items()}
LINKS: dict[tuple, set] = {}
for p in DATA["pokemon"]:
    for other in [("type", t) for t in p["types"]] + [("ability", a) for a in p["abilities"]] + [("move", m) for m in p["moves"]]:
        LINKS.setdefault(("pokemon", p["name"]), set()).add(other)
        LINKS.setdefault(other, set()).add(("pokemon", p["name"]))
for m in DATA["moves"]:
    LINKS.setdefault(("move", m["name"]), set()).add(("type", m["type"]))
    LINKS.setdefault(("type", m["type"]), set()).add(("move", m["name"]))
ALL = {kind: {e for e in NUMBER if e[0] == kind and (kind != "type" or e in LINKS)} for kind in KINDS}

RESOLVER = EntityResolver(Repository(read_json(ROOT / "data" / "pokedex.json")))


def entities(text, candidates):
    """A word's entities: the exact names, else the closest to the full name."""
    exact = [(c.ref.kind.value, c.ref.name) for c in candidates if c.exact]
    if exact:
        return exact
    found = [(c.ref.kind.value, c.ref.name) for c in candidates]
    best = min(OSA.distance(text, normalize(n)) for _, n in found)
    return [e for e in found if OSA.distance(text, normalize(e[1])) == best]


def kind_word(word):
    """The kind a word names (matched like a name), or None."""
    if len(word) < 3:
        return None
    found = [(d, k) for k in KINDS if (d := EntityResolver.distance(word, k)) is not None]
    return min(found)[1] if found else None


def tokens(query):
    """Items (lists of entities) and kind words (strings), labels dropped."""
    words, out, i = normalize(query).split(), [], 0
    while i < len(words):
        whole = RESOLVER.whole_name(words, i)
        if whole:
            out.append(entities(whole[0].query, whole))
            i += len(whole[0].query.split())
            continue
        word = words[i]
        if word not in RESOLVER.names and (k := kind_word(word)):
            out.append(k)
        elif len(word) >= 3 and (found := RESOLVER.resolve(word)):
            out.append(entities(word, found))
        i += 1
    def fits(item, kind):
        return any((e[0], kind) in LINKABLE for e in item)
    kept = []
    for i, t in enumerate(out):
        if isinstance(t, str):
            start = max([j for j in range(i) if isinstance(out[j], str)], default=-1) + 1
            if not any(fits(x, t) for x in out[start:i]):
                next_to = [out[j] for j in (i - 1, i + 1) if 0 <= j < len(out) and isinstance(out[j], list)]
                if any(all(e[0] == t for e in x) for x in next_to):
                    continue  # a label
        kept.append(t)
    return kept, fits


def groups(query):
    """[(kind, items)], or "unchanged" without a kind word, or None when an item has no group."""
    toks, fits = tokens(query)
    if not any(isinstance(t, str) for t in toks):
        return "unchanged"
    def repeats(items, more):
        had = {e[0] for x in items for e in x}
        return any(e[0] in had for x in more for e in x)
    out, pending = [], []
    for t in toks:
        if isinstance(t, list):
            pending.append(t)
            continue
        if out:
            back = [x for x in pending if not fits(x, t) and fits(x, out[-1][0])]
            if repeats(out[-1][1], back):
                return None
            out[-1][1].extend(back)
            pending = [x for x in pending if x not in back]
        out.append((t, pending))
        pending = []
    if repeats(out[-1][1], pending):
        return None
    out[-1][1].extend(pending)
    return out


def lists(query):
    """The expected lists: (kind, filters, chain, entities); "unchanged"; or [] for no results."""
    found = groups(query)
    if found in ("unchanged", None):
        return found or []
    previous = None
    for kind, items in found:
        choices = []
        for item in items:
            usable = [e for e in item if (e[0], kind) in LINKABLE]
            if not usable:
                return []
            choices.append(usable)
        result = []
        for reading in product(*choices):
            by_kind = {}
            for e in reading:
                by_kind.setdefault(e[0], [])
                if e not in by_kind[e[0]]:
                    by_kind[e[0]].append(e)
            for filters in product(*by_kind.values()):
                for chain in previous if previous is not None else [None]:
                    if any(set(r[1]) == set(filters) and r[2] is chain for r in result):
                        continue
                    members = set(ALL[kind])
                    for f in filters:
                        members &= LINKS.get(f, set())
                    if chain is not None:
                        members = {m for m in members if LINKS.get(m, set()) & set(chain[3])}
                    result.append((kind, filters, chain, sorted(members, key=NUMBER.get)))
        previous = result
    return [r for r in previous if r[3]]


def label(entity):
    """An entity's display name: fire-blast -> Fire Blast."""
    return entity[1].replace("-", " ").title()


def phrase(kind, filter_kind):
    """How a filter reads in a heading."""
    if filter_kind == "type" and kind in ("pokemon", "move"):
        return "of type "
    if kind == "pokemon":
        return "with " if filter_kind == "ability" else "that learn "
    return "learned by " if kind == "move" else "of "


def title(result, top=True):
    """A list's heading, as plain text."""
    kind, filters, chain, _ = result
    order = ["type", "ability", "move", "pokemon"]
    filters = sorted(filters, key=lambda f: order.index(f[0]))
    phrases = [phrase(kind, f[0]) + label(f) for f in filters]
    if chain is not None:
        phrases.append(phrase(kind, chain[0]) + title(chain, top=False))
    text = PLURAL[kind] if phrases else "all " + PLURAL[kind]
    if filters and filters[0][0] == "type":  # a type reads like an adjective: no comma or "and" after it
        text += " " + phrases.pop(0)
    for i, p in enumerate(phrases):
        text += (" " if i == 0 else " and " if i == len(phrases) - 1 else ", ") + p
    return text[:1].upper() + text[1:] if top else text


def yaml_text():
    """The whole relations.yaml."""
    lines = [
        "# Labelled cases of the relation search (docs/RELATION_SEARCH.md). Each case: the lists expected, in order:",
        "#   title, count, and the items (all when 10 or fewer, else the first 3: `starts`).",
        "#   unchanged -> no kind word: the name search answers, as before.  none -> no results.",
        "# Written by scripts/relation_cases.py, which computes them from data/pokedex.json independently of the code",
        "# under test; lists are in number order (types: PokeAPI's numbers, Normal 1 … Fairy 18). Edit CASES there.",
    ]
    section = None
    for sec, query, note in CASES:
        if sec != section:
            lines += ["", f"{sec}:"]
            section = sec
        comment = f"  # {note}" if note else ""
        found = lists(query)
        if found in ("unchanged", []):
            lines.append(f"  - {{query: {query}, expect: {'unchanged' if found else 'none'}}}{comment}")
            continue
        lines += [f"  - query: {query}{comment}", "    expect:"]
        for result in found:
            refs = [f"{k}:{n}" for k, n in result[3]]
            key, shown = ("items", refs) if len(refs) <= 10 else ("starts", refs[:3])
            lines.append(f'      - {{title: "{title(result)}", count: {len(refs)}, {key}: [{", ".join(shown)}]}}')
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    text = yaml_text()
    if "--check" in sys.argv:
        same = OUTPUT.read_text(encoding="utf-8") == text
        print("relations.yaml is up to date" if same else "relations.yaml differs: run without --check to rewrite it")
        sys.exit(0 if same else 1)
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}: {len(CASES)} cases")
