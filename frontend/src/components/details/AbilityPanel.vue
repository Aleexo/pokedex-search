<script setup lang="ts">
// An ability's details: its effect, and the Pokémon that have it.
import type { AbilityDetails } from "../../api";
import EntityChips from "../shared/EntityChips.vue";

defineProps<{ ability: AbilityDetails }>();
</script>

<template>
  <p>{{ ability.short_effect }}</p>
  <p><b>Pokémon ({{ ability.pokemon.length }}):</b></p>
  <EntityChips :items="ability.pokemon" />
</template>
