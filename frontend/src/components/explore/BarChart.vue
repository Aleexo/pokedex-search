<script setup lang="ts">
// Horizontal bar chart in plain SVG: one bar per row, lengths proportional to the largest value shown,
// in type colours (two halves for two types). Sizes are SVG units: the SVG scales to its container.
import { computed } from "vue";
import type { Row } from "../../api";
import { open } from "../../state";
import { focusSibling, typeColor } from "../../util";

const props = defineProps<{ rows: Row[] }>();

const WIDTH = 520;
const LABEL_WIDTH = 140;
const ROW_HEIGHT = 26;
const BAR_COLOR = "#3b82f6"; // a row without a type

// Each row with its position, bar width and type colours. The largest value fills the room left after the label.
const bars = computed(() => {
  const max = Math.max(...props.rows.map((r) => r.x), 0) || 1;
  const room = WIDTH - LABEL_WIDTH - 50; // leave space for the value after the bar
  return props.rows.map((r, i) => ({
    ...r, y: i * ROW_HEIGHT, width: Math.max(2, (r.x / max) * room), colors: r.types.map(typeColor),
  }));
});
const height = computed(() => props.rows.length * ROW_HEIGHT + 4);
</script>

<template>
  <svg :viewBox="`0 0 ${WIDTH} ${height}`" class="chart">
    <g v-for="b in bars" :key="b.name" class="bar-row" tabindex="0"
       @click="open(b.kind, b.name)" @keydown.enter="open(b.kind, b.name)"
       @keydown.down.prevent="focusSibling($event, 1)" @keydown.up.prevent="focusSibling($event, -1)">
      <title>{{ b.label }}: {{ b.x }}</title>
      <text :x="LABEL_WIDTH - 6" :y="b.y + 15" text-anchor="end">{{ b.label }}</text>

      <!-- Two types: the bar in two halves, first type on top. SVG fills a shape with one paint, so the paint is a
           gradient whose two colours meet at 50 % with no blend. -->
      <template v-if="b.colors.length === 2">
        <linearGradient :id="`bar-${b.name}`" x1="0" y1="0" x2="0" y2="1">
          <stop offset="50%" :stop-color="b.colors[0]" /><stop offset="50%" :stop-color="b.colors[1]" />
        </linearGradient>
        <rect :x="LABEL_WIDTH" :y="b.y + 2" :width="b.width" height="18" rx="3" :fill="`url(#bar-${b.name})`" />
      </template>
      <!-- One type (or none): the bar in that colour -->
      <rect v-else :x="LABEL_WIDTH" :y="b.y + 2" :width="b.width" height="18" rx="3" :fill="b.colors[0] ?? BAR_COLOR" />

      <text :x="LABEL_WIDTH + b.width + 4" :y="b.y + 15" class="value">{{ b.x }}</text>
    </g>
  </svg>
</template>

<style scoped>
.chart { width: 100%; height: auto; font-size: 12px; }
.bar-row { cursor: pointer; }
.bar-row:hover rect { filter: brightness(0.85); }
.bar-row:focus-visible { outline: none; }
.bar-row:focus-visible rect { stroke: #1e3a8a; stroke-width: 2; }
.value { fill: #555; }
</style>
