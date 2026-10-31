<script setup lang="ts">
// Buttons naming Pokémon, moves or abilities; each opens its own details. Over a name (mouse or keyboard focus), a
// card shows a Pokémon's sprite, name and types, or a move's name, type, class and power; an ability shows its effect.
import type { EntityRef } from "../../api";
import { open } from "../../state";
import { hideImage, typeColor } from "../../util";

// A Pokémon comes with its types and sprite; a move with its type, class and power; an ability with its effect.
type Item = EntityRef & {
  short_effect?: string; types?: string[]; sprite?: string; type?: string; damage_class?: string; power?: number | null;
};

defineProps<{ items: Item[] }>();
</script>

<template>
  <span v-for="e in items" :key="e.name" class="chip-wrap">
    <button class="chip" :title="e.short_effect" @click="open(e.kind, e.name)">{{ e.label }}</button>
    <!-- The cards, shown by CSS while the mouse is over the name or the name has keyboard focus -->
    <!-- A Pokémon: sprite, name, types -->
    <span v-if="e.sprite" class="card" aria-hidden="true">
      <img :src="e.sprite" alt="" @error="hideImage" />
      <b>{{ e.label }}</b>
      <span class="types">
        <span v-for="t in e.types" :key="t" class="type" :style="{ background: typeColor(t) }">{{ t }}</span>
      </span>
    </span>
    <!-- A move: name, type, class (physical, special, status), power ("—" for a status move) -->
    <span v-else-if="e.type" class="card" aria-hidden="true">
      <b>{{ e.label }}</b>
      <span class="types"><span class="type" :style="{ background: typeColor(e.type) }">{{ e.type }}</span></span>
      <span class="power"><span class="class">{{ e.damage_class }}</span> · power {{ e.power ?? "—" }}</span>
    </span>
  </span>
</template>

<style scoped>
.chip-wrap { position: relative; display: inline-block; }
/* Above the name and aligned on its right edge, so a name near the right of the panel doesn't widen the page */
.card { display: none; position: absolute; right: 0; bottom: calc(100% + 4px); z-index: 10; width: max-content;
  padding: 6px 12px 8px; background: white; border: 1px solid #ddd; border-radius: 8px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12); text-align: center; pointer-events: none; }
.chip-wrap:hover .card, .chip-wrap:focus-within .card { display: block; }
.card img { display: block; width: 64px; height: 64px; margin: 0 auto; image-rendering: pixelated; }
.types { display: flex; gap: 3px; justify-content: center; margin-top: 4px; }
.card .type { margin: 0; }
.power { display: block; margin-top: 3px; font-size: 0.8rem; color: #555; }
.class { text-transform: capitalize; }
</style>
