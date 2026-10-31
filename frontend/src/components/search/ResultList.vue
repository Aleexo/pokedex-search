<script setup lang="ts">
// The result rows. Each row: a picture on the right (a Pokémon's sprite, or a type's colour badge), the name and
// kind, the type badges of a Pokémon or move, and a line underneath (why it matched, or the Pokédex number).
import type { Hit } from "../../api";
import { isOpen, open } from "../../state";
import { focusSibling, hideImage, typeColor } from "../../util";
import TypeBadge from "../shared/TypeBadge.vue";

const props = defineProps<{
  hits: Hit[];
  numbered: boolean; // listing all Pokémon: show the Pokédex number instead of why it matched
}>();

/**
 * The line under the name: the Pokédex number when listing all Pokémon, otherwise why it matched.
 * @example subtitle(bulbasaurHit) // "Close to 'bulbi' (possible typo)", or "#1" when listing all Pokémon
 */
const subtitle = (h: Hit): string => (props.numbered ? `#${h.pokemon?.id}` : h.reasons.join(" · "));
</script>

<template>
  <ul>
    <!-- Focusable rows: Tab or ↑/↓ to move, Enter to open -->
    <li v-for="h in hits" :key="h.kind + h.name" tabindex="0" :class="{ active: isOpen(h) }"
        @click="open(h.kind, h.name)" @keydown.enter="open(h.kind, h.name)"
        @keydown.down.prevent="focusSibling($event, 1)" @keydown.up.prevent="focusSibling($event, -1)">
      <!-- 1. Picture on the right, by kind -->
      <img v-if="h.kind === 'pokemon'" :src="h.pokemon?.sprite" alt="" class="hit-sprite" @error="hideImage" />
      <span v-else-if="h.kind === 'type'" class="type hit-type" :style="{ background: typeColor(h.name) }">{{ h.label }}</span>
      <!-- 2. Name and kind -->
      <b>{{ h.label }}</b> <small class="kind">{{ h.kind }}</small>
      <!-- 3. Type badges, for a Pokémon or a move (a type has its badge on the right, an ability has no type) -->
      <template v-if="h.kind === 'pokemon' || h.kind === 'move'">
        <TypeBadge v-for="t in h.types" :key="t" :type="t" />
      </template>
      <!-- 4. Line underneath -->
      <div class="reasons">{{ subtitle(h) }}</div>
    </li>
  </ul>
</template>

<style scoped>
ul { list-style: none; padding: 0; margin: 0; }
li { padding: 8px; border-bottom: 1px solid #eee; cursor: pointer; }
li:hover, li.active { background: #f0f4ff; }
li:focus-visible { outline: 2px solid #2563eb; outline-offset: -2px; }
.hit-sprite { float: right; width: 64px; height: 64px; margin: -12px 0; image-rendering: pixelated; }
.type.hit-type { float: right; font-size: 0.75rem; padding: 2px 8px; margin: 10px 0 0; border-radius: 5px; }
.reasons { color: #555; font-size: 0.85rem; margin-top: 2px; }
</style>
