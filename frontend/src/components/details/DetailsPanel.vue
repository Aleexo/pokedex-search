<script setup lang="ts">
// The details of the open entity: a header (name, kind, close), then one panel per kind.
import { close, coverage, details } from "../../state";
import { typeColor } from "../../util";
import AbilityPanel from "./AbilityPanel.vue";
import MovePanel from "./MovePanel.vue";
import PokemonPanel from "./PokemonPanel.vue";
import TypePanel from "./TypePanel.vue";

defineProps<{ hint: string }>(); // what to click when nothing is open: "a result", "a bar or row"
</script>

<template>
  <p v-if="!details" class="muted">Click {{ hint }} to see its details.</p>

  <div v-else class="details">
    <button class="link close" @click="close">× close</button>
    <h2>
      <span v-if="details.kind === 'type'" class="type title" :style="{ background: typeColor(details.name) }">{{ details.label }}</span>
      <template v-else>{{ details.label }}</template>
      <small class="kind">{{ details.kind }}</small>
      <small v-if="details.kind === 'pokemon'">#{{ details.id }}</small>
    </h2>

    <PokemonPanel v-if="details.kind === 'pokemon'" :pokemon="details" :coverage="coverage" />
    <MovePanel v-else-if="details.kind === 'move'" :move="details" />
    <AbilityPanel v-else-if="details.kind === 'ability'" :ability="details" />
    <TypePanel v-else-if="details.kind === 'type'" :type="details" />
  </div>
</template>

<style scoped>
.details { position: relative; }
.close { position: absolute; right: 0; top: 0; }
.type.title { font-size: 1.3rem; padding: 3px 12px; border-radius: 6px; }
</style>
