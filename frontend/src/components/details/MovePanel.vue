<script setup lang="ts">
// A move's details: its type, class, power, accuracy and PP, its effect, and the Pokémon that learn it.
import type { MoveDetails } from "../../api";
import EntityChips from "../shared/EntityChips.vue";
import TypeBadge from "../shared/TypeBadge.vue";

defineProps<{ move: MoveDetails }>();
</script>

<template>
  <p>
    <TypeBadge :type="move.type" />
    {{ move.damage_class }} · power {{ move.power ?? "—" }} · accuracy {{ move.accuracy ?? "—" }} · PP {{ move.pp }}
  </p>
  <p>{{ move.short_effect }}</p>
  <p><b>Pokémon ({{ move.pokemon.length }}):</b></p>
  <EntityChips :items="move.pokemon" />
</template>
