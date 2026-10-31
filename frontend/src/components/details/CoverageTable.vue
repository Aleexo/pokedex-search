<script setup lang="ts">
// A Pokémon's coverage (docs/MOVE_COVERAGE.md): its walls, then one line per move of another type that gets past them.
import type { Coverage, CoverageMove } from "../../api";
import { open } from "../../state";
import { typeColor } from "../../util";
import TypeBadge from "../shared/TypeBadge.vue";

defineProps<{
  coverage: Coverage;
  ownTypes: string[]; // the Pokémon's types, for "types resisting its Fire / Flying moves"
}>();

/**
 * Physical or special, with the Pokémon's stat the move uses.
 * @example attackClass({ damage_class: "physical", stat: 84 }) // "Physical (Atk 84)"
 */
const attackClass = (m: CoverageMove): string =>
  m.damage_class === "physical" ? `Physical (Atk ${m.stat})` : `Special (Sp. Atk ${m.stat})`;

/**
 * CSS class of a multiplier cell: strong (×2 and more), weak (below ×1), or plain.
 * @example multiplierClass(2) // "mult-strong"
 */
const multiplierClass = (x: number): string => (x >= 2 ? "mult-strong" : x < 1 ? "mult-weak" : "");
</script>

<template>
  <div class="coverage">
    <p><b>Coverage</b></p>
    <!-- Walls: the types resisting all its own types (×0.5 or less) -->
    <!-- The badges on their own row under the label, so that up to 7 walls stay together -->
    <template v-if="coverage.walls.length">
      <p class="walls-label">Walls <small class="muted">(types resisting its {{ ownTypes.join(" / ") }} moves)</small>:</p>
      <div class="walls">
        <TypeBadge v-for="w in coverage.walls" :key="w" :type="w" />
      </div>
    </template>
    <p v-for="n in coverage.notes" :key="n" class="muted">{{ n }}</p>

    <!-- One line per move, with how many walls it hits ×2 and ×1; the estimated damage (tie-break) is not shown -->
    <template v-if="coverage.moves.length">
      <p class="coverage-title">Widest coverage <small class="muted">(moves of other types than its own)</small></p>
      <div class="coverage-scroll">
        <table class="coverage-table">
          <thead>
            <tr>
              <th>Move</th><th>Type</th><th>Class</th><th>Power</th><th>Accuracy</th><th>PP</th>
              <!-- The wall columns sit between two bars: one before the first (walls-start), one after the last (walls-end) -->
              <th v-for="(w, i) in coverage.walls" :key="w" :title="w" :class="{ 'walls-start': i === 0 }">
                <span class="type" :style="{ background: typeColor(w) }">{{ w.slice(0, 3) }}</span>
              </th>
              <th class="walls-end" title="walls hit ×2">×2</th><th title="walls hit ×1">×1</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in coverage.moves" :key="m.name">
              <td><button class="chip" @click="open('move', m.name)">{{ m.label }}</button></td>
              <td><TypeBadge :type="m.type" /></td>
              <td>{{ attackClass(m) }}</td>
              <td>{{ m.power }}</td>
              <td>{{ m.accuracy === null ? "—" : m.accuracy + " %" }}</td>
              <td>{{ m.pp }}</td>
              <td v-for="(w, i) in coverage.walls" :key="w" :class="[multiplierClass(m.multipliers[w]), { 'walls-start': i === 0 }]">×{{ m.multipliers[w] }}</td>
              <td class="walls-end">{{ m.hits }}</td><td>{{ m.neutral }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<style scoped>
.coverage { margin-top: 12px; }
.walls-label { margin-bottom: 4px; }
.walls { display: flex; flex-wrap: wrap; gap: 4px; }
.walls .type { margin: 0; }
.coverage-title { margin: 10px 0 4px; font-weight: 600; }
.coverage-scroll { overflow-x: auto; max-width: 100%; }
.coverage-table { border-collapse: collapse; font-size: 0.9rem; }
.coverage-table th { text-align: left; font-size: 0.75rem; color: #555; padding: 2px 8px 2px 0; }
.coverage-table td { padding: 3px 8px 3px 0; white-space: nowrap; }
.coverage-table .walls-start, .coverage-table .walls-end { border-left: 1px solid #ccc; padding-left: 8px; }
.mult-strong { color: #15803d; font-weight: 600; }
.mult-weak { color: #b91c1c; }
</style>
