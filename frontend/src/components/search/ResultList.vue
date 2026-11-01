<script setup lang="ts">
// The result rows. Each row: a picture on the right (a Pokémon's sprite, or a type's colour badge), the name and
// kind, the type badges of a Pokémon or move, and a line underneath (why it matched, or the Pokédex number).
// A relation search's lists are folded, like the moves in the details panel: an arrow and the heading (text, with
// its entities as badges or chips) and the count; a click unfolds the rows, 20 per page with the list's own pager.
// Which lists are open, and on which page, is a v-model (`lists`) that SearchView keeps in the URL.
import { computed } from "vue";
import type { Group, Hit } from "../../api";
import { isOpen, open } from "../../state";
import { focusSibling, hideImage, typeColor } from "../../util";
import EntityChips from "../shared/EntityChips.vue";
import TypeBadge from "../shared/TypeBadge.vue";

const props = defineProps<{
  hits: Hit[];
  numbered: boolean; // listing all Pokémon: show the Pokédex number instead of why it matched
  groups?: Group[]; // a relation search's lists
}>();

/**
 * The rows by list: one section per relation list, with its heading; a name search is one section without.
 * @example sections.value // [{ group: groups[0], hits: [charmander, …] }, { group: groups[1], hits: [bulbasaur, …] }]
 */
const sections = computed((): { group?: Group; hits: Hit[] }[] =>
  props.groups?.length
    ? props.groups.map((group, i) => ({ group, hits: props.hits.filter((h) => h.group === i) }))
    : [{ hits: props.hits }],
);

const LIST_PAGE = 20; // rows per page inside a relation list, as the name search's pages

// Each relation list's state, by its index: 0 folded, n open on page n (missing: folded).
const lists = defineModel<number[]>("lists", { required: true });

/**
 * Set the state of list `i`, leaving the others as they are.
 * @example setList(1, 2) // [0, 0] -> [0, 2]: the second list open on page 2
 */
function setList(i: number, value: number): void {
  const next = sections.value.map((_, j) => lists.value[j] ?? 0);
  next[i] = value;
  lists.value = next;
}

/**
 * The page shown of section `i`: its list's page (1 while folded), within its pages.
 * @example page(0) // 2 after Next in a list of 34 rows
 */
const page = (i: number): number => Math.min(Math.max(lists.value[i] ?? 0, 1), pages(i));

/**
 * A list was unfolded or folded by a click: keep it in its state (open on page 1, or folded).
 * @example onToggle(0, event) // unfolding the first list: lists [0, 0] -> [1, 0]
 */
function onToggle(i: number, event: Event): void {
  const unfolded = (event.target as HTMLDetailsElement).open;
  if (unfolded !== (lists.value[i] ?? 0) > 0) setList(i, unfolded ? 1 : 0);
}

/**
 * The rows shown of section `i`: a relation list's current page, or all the rows of a name search's page.
 * @example shown(0) // rows 1-20 of the first list; after Next, rows 21-34
 */
const shown = (i: number): Hit[] => {
  const s = sections.value[i];
  if (!s.group) return s.hits;
  return s.hits.slice((page(i) - 1) * LIST_PAGE, page(i) * LIST_PAGE);
};

/**
 * Number of pages of section `i` (1 for a name search: its pages come from the API).
 * @example pages(0) // 2 for a list of 34 rows
 */
const pages = (i: number): number => (sections.value[i].group ? Math.ceil(sections.value[i].hits.length / LIST_PAGE) : 1);

/**
 * The line under the name: the Pokédex number when listing all Pokémon, otherwise why it matched.
 * @example subtitle(bulbasaurHit) // "Close to 'bulbi' (possible typo)", or "#1" when listing all Pokémon
 */
const subtitle = (h: Hit): string => (props.numbered ? `#${h.pokemon?.id}` : h.reasons.join(" · "));
</script>

<template>
  <!-- A relation list: folded, its heading as the summary; a name search: the rows only -->
  <component :is="s.group ? 'details' : 'div'" v-for="(s, i) in sections" :key="i"
             :open="s.group ? (lists[i] ?? 0) > 0 : undefined" @toggle="onToggle(i, $event)">
    <summary v-if="s.group">
      <template v-for="(part, j) in s.group.heading" :key="j">
        <template v-if="typeof part === 'string'">{{ part }}</template>
        <TypeBadge v-else-if="part.kind === 'type'" :type="part.name" />
        <EntityChips v-else :items="[part]" />
      </template>
      <small>({{ s.group.total }})</small>
    </summary>
  <ul>
    <!-- Focusable rows: Tab or ↑/↓ to move, Enter to open -->
    <li v-for="h in shown(i)" :key="h.kind + h.name" tabindex="0" :class="{ active: isOpen(h) }"
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
  <!-- A long relation list: its own pages -->
  <p v-if="pages(i) > 1" class="pager">
    <button :disabled="page(i) === 1" @click="setList(i, page(i) - 1)">‹ Previous</button>
    <span>Page {{ page(i) }} / {{ pages(i) }}</span>
    <button :disabled="page(i) === pages(i)" @click="setList(i, page(i) + 1)">Next ›</button>
  </p>
  </component>
</template>

<style scoped>
ul { list-style: none; padding: 0; margin: 0; }
li { padding: 8px; border-bottom: 1px solid #eee; cursor: pointer; }
li:hover, li.active { background: #f0f4ff; }
summary { padding: 10px 8px; border-bottom: 1px solid #eee; cursor: pointer; font-weight: 600; }
li:focus-visible { outline: 2px solid #2563eb; outline-offset: -2px; }
.hit-sprite { float: right; width: 64px; height: 64px; margin: -12px 0; image-rendering: pixelated; }
.type.hit-type { float: right; font-size: 0.75rem; padding: 2px 8px; margin: 10px 0 0; border-radius: 5px; }
.reasons { color: #555; font-size: 0.85rem; margin-top: 2px; }
.pager { display: flex; align-items: center; gap: 12px; padding-left: 8px; }
</style>
