<script setup lang="ts" generic="T extends string">
// Two or more buttons side by side, one of them on (v-model): Pokémon / Moves, Chart / Table.
const value = defineModel<T>({ required: true });
defineProps<{ options: { value: T; label: string }[] }>();
</script>

<template>
  <div class="toggle" role="group">
    <button v-for="o in options" :key="o.value" type="button" :class="{ on: value === o.value }" @click="value = o.value">{{ o.label }}</button>
  </div>
</template>

<style scoped>
.toggle { display: flex; }
button { padding: 4px 12px; border-radius: 0; }
button:first-child { border-radius: 6px 0 0 6px; }
button:last-child { border-radius: 0 6px 6px 0; border-left: none; }
button.on { background: #2563eb; color: white; border-color: #2563eb; }
</style>
