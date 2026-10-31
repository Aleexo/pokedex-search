<script setup lang="ts">
// Explore's sidebar: group by (one row each, or by type), the field to rank by, highest or lowest.
import type { Fields, Subject } from "../../api";

const byType = defineModel<boolean>("byType", { required: true });
const x = defineModel<string>("x", { required: true });
const order = defineModel<string>("order", { required: true });
defineProps<{
  numbers: Fields["numbers"]; // the fields of the current subject
  subject: Subject;
}>();
</script>

<template>
  <aside>
    <form @submit.prevent>
      <h3>Chart</h3>
      <label>Group by
        <select v-model="byType">
          <option :value="false">{{ subject === "move" ? "Move" : "Pokémon" }}</option>
          <option :value="true">Type</option>
        </select>
      </label>
      <label>Rank by
        <select v-model="x">
          <option v-for="n in numbers" :key="n.name" :value="n.name">{{ n.label }}</option>
        </select>
      </label>
      <label>Show
        <select v-model="order">
          <option value="top">Highest</option>
          <option value="bottom">Lowest</option>
        </select>
      </label>
    </form>
  </aside>
</template>

<style scoped>
form { display: flex; flex-direction: column; gap: 12px; padding-top: 16px; }
label { display: flex; flex-direction: column; font-size: 0.8rem; color: #555; gap: 2px; }
select { width: 100%; box-sizing: border-box; padding: 6px; font-size: 0.95rem; border: 1px solid #ccc; border-radius: 6px; }
h3 { font-size: 0.95rem; margin: 0 0 -4px; }
</style>
