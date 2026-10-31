<script setup lang="ts">
// Explore tab (docs/EXPLORE.md): the menus and type filter, then the 8 rows as a bar chart or a table,
// next to the details panel. Every choice is kept in the URL, so a chart can be shared.
import { computed, onActivated, onMounted, reactive, ref, watch } from "vue";
import { getJson, type Explored, type Fields, type Subject } from "../../api";
import { error } from "../../state";
import BarChart from "./BarChart.vue";
import DetailsPanel from "../details/DetailsPanel.vue";
import ExploreMenus from "./ExploreMenus.vue";
import ExploreTable from "./ExploreTable.vue";
import ToggleButtons from "../shared/ToggleButtons.vue";
import TypeFilter from "./TypeFilter.vue";

const params = new URLSearchParams(location.search);
const fields = ref<Fields | null>(null); // the menus, from the API
const explored = ref<Explored | null>(null); // the last rows received
const display = ref<"chart" | "table">(params.get("display") === "table" ? "table" : "chart");
// The menus' choices, starting from the URL (?view=explore&x=attack&by_type=true&types=fire...).
const choice = reactive({
  x: params.get("x") ?? "speed",
  by_type: params.get("by_type") === "true",
  order: params.get("order") ?? "top",
  types: params.getAll("types"), // the type filter: Pokémon with any of these types, or moves of them
});

// The field decides the subject (Power ranks moves), so the subject isn't stored.
const subject = computed<Subject>(() => fields.value?.numbers.find((n) => n.name === choice.x)?.subject ?? "pokemon");
const numbersForSubject = computed(() => fields.value?.numbers.filter((n) => n.subject === subject.value) ?? []);
const xLabel = computed(() => fields.value?.numbers.find((n) => n.name === explored.value?.x)?.label ?? "");
const rowLabel = computed(() => {
  const e = explored.value;
  return !e ? "" : e.by_type ? "Type" : e.subject === "move" ? "Move" : "Pokémon";
});
const title = computed(() =>
  explored.value ? `${rowLabel.value}: ${xLabel.value}, ${explored.value.order === "top" ? "highest" : "lowest"}` : "");
// What the values mean, under the chart: averages for types, moves without a value left out.
const note = computed(() => {
  const e = explored.value;
  if (!e) return "";
  if (e.by_type) {
    return e.subject === "move"
      ? "Values are averages over each type's moves that have a value for the chosen field."
      : "Values are averages over the Pokémon in each group.";
  }
  return e.subject === "move" ? "Moves without a value for the chosen field (e.g. status moves have no power) are left out." : "";
});

// The Pokémon / Moves switch: switching picks the first field of the other subject (HP, or Power).
const subjectSwitch = computed({
  get: () => subject.value,
  set: (name: Subject) => {
    const first = fields.value?.numbers.find((n) => n.subject === name);
    if (first && name !== subject.value) choice.x = first.name;
  },
});

/**
 * Query string of the current choices; the type filter is left out when grouping by type.
 * @example apiParams().toString() // "x=attack&order=top&types=fire"
 */
function apiParams(): URLSearchParams {
  const q = new URLSearchParams({ x: choice.x, order: choice.order });
  if (choice.by_type) q.set("by_type", "true");
  else for (const t of choice.types) q.append("types", t);
  return q;
}

/**
 * Page URL that reopens Explore as it is now, chart or table included.
 * @example pageUrl() // "?view=explore&x=attack&order=top&display=table"
 */
function pageUrl(): string {
  const q = apiParams();
  if (display.value === "table") q.set("display", "table");
  return `?view=explore&${q}`;
}

/**
 * Fetch the rows for the current choices and put them in the URL.
 * @example explore() // with x=speed, by_type: explored.value.rows[0].name -> "electric"
 */
async function explore(): Promise<void> {
  history.replaceState(null, "", pageUrl());
  try {
    explored.value = await getJson<Explored>(`/api/explore?${apiParams()}`);
  } catch (e) {
    error.value = String(e);
  }
}

onMounted(async () => {
  try {
    fields.value = await getJson<Fields>("/api/explore/fields");
  } catch (e) {
    error.value = String(e);
    return;
  }
  // An old link may name a field that no longer exists (x=total): use the first one; the watcher redraws.
  if (!fields.value.numbers.some((n) => n.name === choice.x)) choice.x = fields.value.numbers[0].name;
  else await explore();
});
watch(choice, explore); // any menu change redraws
watch(display, () => history.replaceState(null, "", pageUrl()));
onActivated(() => history.replaceState(null, "", pageUrl())); // the tab is shown again: its URL comes back
</script>

<template>
  <!-- What to rank: Pokémon or moves, each alone or by type -->
  <ToggleButtons v-model="subjectSwitch" class="subject" aria-label="Explore"
                 :options="[{ value: 'pokemon', label: 'Pokémon' }, { value: 'move', label: 'Moves' }]" />

  <div v-if="explored && fields" class="columns with-sidebar">
    <ExploreMenus v-model:by-type="choice.by_type" v-model:x="choice.x" v-model:order="choice.order"
                  :numbers="numbersForSubject" :subject="subject" />

    <section>
      <TypeFilter v-model="choice.types" :options="fields.filters.types" :disabled="choice.by_type" :explored="explored" />

      <div class="chart-head">
        <h2>{{ title }}</h2>
        <ToggleButtons v-model="display" aria-label="Display"
                       :options="[{ value: 'chart', label: 'Chart' }, { value: 'table', label: 'Table' }]" />
      </div>
      <p v-if="!explored.rows.length" class="note">Nothing matches these filters.</p>
      <BarChart v-else-if="display === 'chart'" :rows="explored.rows" />
      <ExploreTable v-else :explored="explored" :row-label="rowLabel" :x-label="xLabel" />

      <p v-if="explored.tied_beyond" class="muted">
        + {{ explored.tied_beyond }} more tied at {{ explored.rows[explored.rows.length - 1].x }}, not shown (only 8 rows; ties are in name order).
      </p>
      <p v-if="note" class="muted">{{ note }}</p>
    </section>

    <section><DetailsPanel hint="a bar or row" /></section>
  </div>
</template>

<style scoped>
.subject { margin-bottom: 4px; }
.chart-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
</style>
