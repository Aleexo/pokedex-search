<script setup lang="ts">
// The type filter above the chart: type badges to switch on or off ("any of"), and how many rows pass it.
// Greyed out when grouping by type: one or the other.
import type { EntityRef, Explored } from "../../api";
import { typeColor } from "../../util";

const chosen = defineModel<string[]>({ required: true }); // the types switched on (v-model)
defineProps<{
  options: EntityRef[]; // the types offered
  disabled: boolean; // grouping by type
  explored: Explored; // for "44 of 151 Pokémon"
}>();

/**
 * Switch one type on or off.
 * @example toggle("fire") // chosen: [] -> ["fire"] -> []
 */
function toggle(name: string): void {
  chosen.value = chosen.value.includes(name) ? chosen.value.filter((t) => t !== name) : [...chosen.value, name];
}
</script>

<template>
  <div class="explore-filters" :class="{ disabled }">
    <div class="filter-types">
      <div class="filter-label">Types <small>(any of)</small></div>
      <div class="type-filter">
        <button v-for="t in options" :key="t.name" type="button" class="type" :disabled="disabled"
                :class="{ off: !chosen.includes(t.name) }" :style="{ background: typeColor(t.name) }"
                @click="toggle(t.name)">{{ t.label }}</button>
      </div>
    </div>
    <p v-if="disabled" class="muted">
      The type filter applies when ranking individual {{ explored.noun }}, not when grouping by type.
    </p>
    <p v-else class="muted">
      {{ explored.matched }} of {{ explored.total }} {{ explored.noun }}
      <button v-if="chosen.length" type="button" class="link" @click="chosen = []">Clear filters</button>
    </p>
  </div>
</template>

<style scoped>
.explore-filters { display: flex; flex-wrap: wrap; gap: 12px 16px; align-items: flex-start; padding: 12px; margin-top: 16px; background: white; border: 1px solid #e5e7eb; border-radius: 8px; }
.filter-types { flex-basis: 100%; display: flex; flex-direction: column; gap: 4px; }
.filter-label { font-size: 0.8rem; color: #555; }
.muted { flex-basis: 100%; margin: 0; }
.type-filter { display: flex; flex-wrap: wrap; gap: 4px; }
.type-filter .type { margin: 0; }
.type.off { opacity: 0.3; }
.disabled .type-filter { opacity: 0.4; }
.disabled .type { cursor: not-allowed; }
</style>
