// The shapes of the API's JSON responses (backend/api/main.py), and one function to fetch them.

export type Kind = "pokemon" | "move" | "ability" | "type";
export type Subject = "pokemon" | "move";

/** Any entity, as the API names it: `{ kind: "move", name: "thunder-wave", label: "Thunder Wave" }`. */
export interface EntityRef {
  kind: Kind;
  name: string;
  label: string;
}

/** A Pokémon named in the details, with what its hover card shows: types and sprite. */
export interface PokemonRef extends EntityRef {
  types: string[];
  sprite: string;
}

/** A move named in the details, with what its hover card shows: type, class, power (null for a status move). */
export interface MoveRef extends EntityRef {
  type: string;
  damage_class: string; // physical, special or status
  power: number | null;
}

/** What a Pokémon row shows: number, types, stats, size, sprite. */
export interface PokemonSummary {
  id: number;
  types: string[];
  stats: Record<string, number>; // hp, attack, defense, special_attack, special_defense, speed
  height_m: number;
  weight_kg: number;
  sprite: string;
}

/** One result row: a search hit, or a Pokémon in the list of all Pokémon. */
export interface Hit extends EntityRef {
  types: string[];
  reasons: string[]; // why it matched; empty when listing all Pokémon
  score?: number;
  pokemon?: PokemonSummary;
}

/** `/api/search` and `/api/pokemon`: one page of result rows. `query` is "" for the list of all Pokémon. */
export interface SearchResult {
  query: string;
  hits: Hit[]; // this page's rows
  notes: string[];
  page: number;
  pages: number;
  total: number; // rows over all pages
}

// `/api/entity/{kind}/{name}`: the details differ per kind; `kind` tells which one it is.
export interface PokemonDetails extends EntityRef, PokemonSummary {
  kind: "pokemon";
  genus: string;
  description: string;
  abilities: (EntityRef & { short_effect: string })[];
  moves: MoveRef[];
  evolution_family: PokemonRef[];
}
export interface MoveDetails extends EntityRef {
  kind: "move";
  type: string;
  power: number | null;
  accuracy: number | null;
  pp: number;
  damage_class: string;
  short_effect: string;
  pokemon: PokemonRef[];
}
export interface AbilityDetails extends EntityRef {
  kind: "ability";
  short_effect: string;
  pokemon: PokemonRef[];
}
export interface TypeDetails extends EntityRef {
  kind: "type";
  pokemon: PokemonRef[];
  moves: MoveRef[];
}
export type Details = PokemonDetails | MoveDetails | AbilityDetails | TypeDetails;

/** One coverage move, as seen by the Pokémon: the stat it uses and its multiplier on each wall. */
export interface CoverageMove extends EntityRef {
  type: string;
  power: number;
  accuracy: number | null;
  pp: number;
  damage_class: "physical" | "special";
  stat: number;
  multipliers: Record<string, number>;
  hits: number; // walls it hits ×2
  neutral: number; // walls it hits ×1
}

/** `/api/coverage/{name}`. */
export interface Coverage {
  pokemon: string;
  walls: string[];
  notes: string[];
  moves: CoverageMove[];
}

/** `/api/explore/fields`: the menus of Explore. */
export interface Fields {
  numbers: { name: string; label: string; subject: Subject }[];
  max_rows: number;
  filters: { types: EntityRef[] };
}

/** One bar or table row of Explore. */
export interface Row extends EntityRef {
  x: number;
  count: number;
  types: string[];
}

/** `/api/explore`: the rows, and what they are. */
export interface Explored {
  x: string;
  subject: Subject;
  by_type: boolean;
  order: "top" | "bottom";
  matched: number;
  total: number;
  noun: string;
  tied_beyond: number;
  rows: Row[];
}

/**
 * GET a URL and parse the JSON body. Throws with the status and body on HTTP errors.
 * @example const spore = await getJson<MoveDetails>("/api/entity/move/spore"); // spore.pokemon -> [Paras, Parasect]
 */
export async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}
