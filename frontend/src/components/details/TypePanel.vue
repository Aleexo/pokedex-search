<script setup lang="ts">
// A type's details: the Pokémon of that type, and its moves.
import type { TypeDetails } from "../../api";
import EntityChips from "../shared/EntityChips.vue";

defineProps<{ type: TypeDetails }>();
</script>

<template>
  <p><b>Pokémon ({{ type.pokemon.length }}):</b></p>
  <EntityChips :items="type.pokemon" />
  <p><b>Moves ({{ type.moves.length }}):</b></p>
  <EntityChips :items="type.moves" />
  <p v-if="!type.moves.length" class="muted">No Gen 1 move has this type.</p>
</template>
