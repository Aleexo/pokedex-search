// State shared by the whole page: the entity open in the details panel, and the last error.
// Components import what they need (`open`, `isOpen`, `error`…) instead of passing it along as props and events.
import { ref } from "vue";
import { getJson, type Coverage, type Details, type Kind } from "./api";

export const details = ref<Details | null>(null); // the entity open in the details panel
export const coverage = ref<Coverage | null>(null); // its coverage moves, for a Pokémon
export const error = ref(""); // shown under the tabs; "" = no error

let lastOpened = ""; // the entity asked for last, so a slower earlier answer doesn't replace it

/**
 * Load one entity, and a Pokémon's coverage, into the details panel.
 * @example open("pokemon", "pikachu") // details.value.evolution_family -> [Pikachu, Raichu]
 */
export async function open(kind: Kind, name: string): Promise<void> {
  const opening = (lastOpened = `${kind}/${name}`);
  try {
    const entity = await getJson<Details>(`/api/entity/${kind}/${name}`);
    const moves = kind === "pokemon" ? await getJson<Coverage>(`/api/coverage/${name}`) : null;
    if (opening !== lastOpened) return; // another entity was clicked meanwhile: its answer wins
    details.value = entity;
    coverage.value = moves;
  } catch (e) {
    error.value = String(e);
  }
}

/**
 * Close the details panel.
 * @example close() // details.value -> null
 */
export function close(): void {
  details.value = null;
}

/**
 * Whether this entity is the one open, so its row can be highlighted.
 * @example isOpen({ kind: "pokemon", name: "pikachu" }) // true after open("pokemon", "pikachu")
 */
export function isOpen(entity: { kind: Kind; name: string }): boolean {
  return details.value?.kind === entity.kind && details.value?.name === entity.name;
}
