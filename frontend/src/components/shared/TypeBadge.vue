<script setup lang="ts">
// A type badge in the type's colour; a click opens the type (and doesn't also click the row around it).
import { open } from "../../state";
import { typeColor } from "../../util";

defineProps<{ type: string }>();
</script>

<template>
  <button class="type" :style="{ background: typeColor(type) }" @click.stop="open('type', type)">{{ type }}</button>
</template>
