<script setup lang="ts">
// A Pokémon's details: sprite, types, size, description, stats, evolution family, abilities, moves, coverage.
import type { Coverage, PokemonDetails } from "../../api";
import { STAT_LABELS, hideImage } from "../../util";
import CoverageTable from "./CoverageTable.vue";
import EntityChips from "../shared/EntityChips.vue";
import TypeBadge from "../shared/TypeBadge.vue";

defineProps<{
  pokemon: PokemonDetails;
  coverage: Coverage | null;
}>();
</script>

<template>
  <img :src="pokemon.sprite" :alt="pokemon.label" @error="hideImage" />
  <p>
    <TypeBadge v-for="t in pokemon.types" :key="t" :type="t" />
    {{ pokemon.genus }} · {{ pokemon.height_m }} m · {{ pokemon.weight_kg }} kg
  </p>
  <p class="muted">{{ pokemon.description }}</p>
  <div v-for="(value, stat) in pokemon.stats" :key="stat" class="stat">
    <span>{{ STAT_LABELS[stat] }}</span>
    <div class="bar"><div :style="{ width: (value / 255) * 100 + '%' }"></div></div>
    <span>{{ value }}</span>
  </div>
  <p><b>Evolution family:</b><EntityChips :items="pokemon.evolution_family" /></p>
  <p><b>Abilities:</b><EntityChips :items="pokemon.abilities" /></p>
  <details>
    <summary><b>Moves ({{ pokemon.moves.length }})</b></summary>
    <EntityChips :items="pokemon.moves" />
  </details>
  <CoverageTable v-if="coverage && coverage.pokemon === pokemon.name" :coverage="coverage" :own-types="pokemon.types" />
</template>

<style scoped>
img { width: 96px; height: 96px; image-rendering: pixelated; }
.stat { display: grid; grid-template-columns: 36px 1fr 36px; gap: 8px; align-items: center; font-size: 0.85rem; }
.bar { background: #eee; height: 8px; border-radius: 4px; overflow: hidden; }
.bar div { background: #3b82f6; height: 100%; }
</style>
