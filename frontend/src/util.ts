// Small helpers shared by the components.

const TYPE_COLORS: Record<string, string> = {
  normal: "#a8a77a", fire: "#ee8130", water: "#6390f0", electric: "#f7d02c", grass: "#7ac74c",
  ice: "#96d9d6", fighting: "#c22e28", poison: "#a33ea1", ground: "#e2bf65", flying: "#a98ff3",
  psychic: "#f95587", bug: "#a6b91a", rock: "#b6a136", ghost: "#735797", dragon: "#6f35fc",
  dark: "#705746", steel: "#b7b7ce", fairy: "#d685ad",
};

/**
 * Badge colour of a type, grey if unknown.
 * @example typeColor("fire") // "#ee8130"
 */
export const typeColor = (type: string): string => TYPE_COLORS[type] ?? "#888";

/** Short stat names for the details panel, keyed like the API's `stats`. */
export const STAT_LABELS: Record<string, string> = {
  hp: "HP", attack: "Atk", defense: "Def", special_attack: "SpA", special_defense: "SpD", speed: "Spe",
};

/**
 * Move keyboard focus to the next or previous row (results, bars, table rows).
 * @example <li @keydown.down.prevent="focusSibling($event, 1)"> // ↓ focuses the row below
 */
export function focusSibling(event: KeyboardEvent, step: number): void {
  const row = event.currentTarget as Element;
  const next = step > 0 ? row.nextElementSibling : row.previousElementSibling;
  (next as HTMLElement | null)?.focus();
}

/**
 * Hide an image that can't load (sprites are remote URLs: offline, they would show as broken).
 * @example <img :src="sprite" @error="hideImage" />
 */
export function hideImage(event: Event): void {
  (event.target as HTMLElement).style.display = "none";
}
