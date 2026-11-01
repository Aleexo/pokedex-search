<script setup lang="ts">
// Search tab: the search box, then the results next to the details panel. The results are the matches of the
// search, or all Pokémon when the box is empty; either list is shown page by page.
import { computed, onActivated, ref, watch } from "vue";
import { getJson, type SearchResult } from "../../api";
import { close, error } from "../../state";
import DetailsPanel from "../details/DetailsPanel.vue";
import ResultList from "./ResultList.vue";

const EXAMPLES = ["pikachu", "bulbi", "pikchu", "beam", "char", "psychic", "thunder wave", "mr mime", "poison moves", "fire pokemon ability blaze"];

const params = new URLSearchParams(location.search);
const query = ref(params.get("q") ?? ""); // the text in the box
const result = ref<SearchResult | null>(null); // the page of results shown

/**
 * The relation lists' state from the URL: one number per list, 0 folded, n open on page n.
 * @example parseLists("2,0") // [2, 0]; parseLists(null) // []
 */
const parseLists = (text: string | null): number[] => (text ? text.split(",").map((n) => Math.max(0, Number(n) || 0)) : []);
const lists = ref<number[]>(parseLists(params.get("lists"))); // which relation lists are open, on which page

// Which list is shown: all Pokémon (searched with an empty box), or the matches of a search.
const allPokemon = computed(() => !result.value?.query.trim());

/**
 * The URL of what is shown, so it can be shared: the search and the page, each only when there is one.
 * @example url() // "?q=char", "?q=char&page=2", "?page=2", or "?" for page 1 of all Pokémon
 */
function url(): string {
  const q = new URLSearchParams();
  if (result.value?.query.trim()) q.set("q", result.value.query);
  if (result.value && result.value.page > 1) q.set("page", String(result.value.page));
  if (lists.value.some((n) => n > 0)) q.set("lists", lists.value.join(","));
  return `?${q}`;
}

/**
 * Show one page of results: the matches of `q`, or all Pokémon when `q` is empty. Closes the details panel and
 * updates the URL. A page that doesn't exist (an old ?page=99 link) shows page 1. A new search folds every relation
 * list; the first load keeps the lists' state from the URL (`keepLists`).
 * @example search("bulbi") // result.value.hits[0].name -> "bulbasaur"; URL becomes ?q=bulbi
 * @example search("", 2)   // all Pokémon, page 2: result.value.hits[0].name -> "spearow"; URL becomes ?page=2
 */
async function search(q = query.value, page = 1, keepLists = false): Promise<void> {
  query.value = q;
  if (!keepLists) lists.value = [];
  close();
  error.value = "";
  const apiUrl = q.trim() ? `/api/search?q=${encodeURIComponent(q)}&page=${page}` : `/api/pokemon?page=${page}`;
  try {
    result.value = await getJson<SearchResult>(apiUrl);
    history.replaceState(null, "", url());
  } catch (e) {
    if (page > 1) return search(q, 1);
    error.value = String(e);
  }
}

// First load from the URL; when the tab is shown again, its URL comes back.
search(query.value, Number(params.get("page")) || 1, true);
watch(lists, () => history.replaceState(null, "", url())); // unfolding a list or turning its page: in the URL
onActivated(() => history.replaceState(null, "", url()));
</script>

<template>
  <form @submit.prevent="search()">
    <input v-model="query" placeholder="A Pokémon, move, ability or type name" autofocus autocomplete="off" />
    <button>Search</button>
  </form>
  <p class="examples">
    Try:
    <button v-for="ex in EXAMPLES" :key="ex" class="link" @click="search(ex)">{{ ex }}</button>
    · <button class="link" @click="search('')">all Pokémon</button>
  </p>

  <template v-if="result">
    <p v-for="note in result.notes" :key="note" class="note">{{ note }}</p>
    <div class="columns">
      <section>
        <h2 v-if="result.total">
          {{ allPokemon ? "All Pokémon" : "Matches" }}
          <small>({{ result.total }})<template v-if="result.pages > 1"> · page {{ result.page }} / {{ result.pages }}</template></small>
        </h2>
        <ResultList v-model:lists="lists" :hits="result.hits" :numbered="allPokemon" :groups="result.groups" />
        <!-- Previous / Next search again with the query of the results shown, not what the box holds now -->
        <p v-if="result.pages > 1" class="pager">
          <button :disabled="result.page === 1" @click="search(result.query, result.page - 1)">‹ Previous</button>
          <span>Page {{ result.page }} / {{ result.pages }}</span>
          <button :disabled="result.page === result.pages" @click="search(result.query, result.page + 1)">Next ›</button>
        </p>
      </section>
      <section><DetailsPanel hint="a result" /></section>
    </div>
  </template>
</template>

<style scoped>
form { display: flex; gap: 8px; }
input { flex: 1; padding: 10px; font-size: 1rem; border: 1px solid #ccc; border-radius: 6px; }
.examples { color: #666; font-size: 0.85rem; }
.pager { display: flex; align-items: center; gap: 12px; }
</style>
