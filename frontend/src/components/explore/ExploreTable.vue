<script setup lang="ts">
// The Explore rows as a table: rank, name, value and, except for single Pokémon, the count behind the value.
import { computed } from "vue";
import type { Explored } from "../../api";
import { isOpen, open } from "../../state";
import { focusSibling } from "../../util";

const props = defineProps<{
  explored: Explored;
  rowLabel: string; // "Pokémon", "Move" or "Type"
  xLabel: string; // the field, e.g. "Speed"
}>();

// The count column: Pokémon (or moves) averaged for a type, Pokémon learning it for a move; none for a Pokémon.
const countLabel = computed(() => {
  const e = props.explored;
  if (!e.by_type) return e.subject === "move" ? "Learned by" : null;
  return e.subject === "move" ? "Moves" : "Pokémon";
});
</script>

<template>
  <table class="explore-table">
    <thead>
      <tr><th>#</th><th>{{ rowLabel }}</th><th>{{ xLabel }}</th><th v-if="countLabel">{{ countLabel }}</th></tr>
    </thead>
    <tbody>
      <tr v-for="(r, i) in explored.rows" :key="r.name" tabindex="0"
          :class="{ active: isOpen(r) }"
          @click="open(r.kind, r.name)" @keydown.enter="open(r.kind, r.name)"
          @keydown.down.prevent="focusSibling($event, 1)" @keydown.up.prevent="focusSibling($event, -1)">
        <td>{{ i + 1 }}</td><td>{{ r.label }}</td><td>{{ r.x }}</td><td v-if="countLabel">{{ r.count }}</td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.explore-table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 0.9rem; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #eee; }
tbody tr { cursor: pointer; }
tbody tr:hover, tbody tr.active { background: #f0f4ff; }
tr:focus-visible { outline: 2px solid #2563eb; outline-offset: -2px; }
</style>
