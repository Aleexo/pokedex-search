<script setup lang="ts">
// The page: title, Search / Explore tabs, and the view shown.
import { ref } from "vue";
import ExploreView from "./components/explore/ExploreView.vue";
import SearchView from "./components/search/SearchView.vue";
import { close, error } from "./state";

type View = "search" | "explore";

const view = ref<View>(new URLSearchParams(location.search).get("view") === "explore" ? "explore" : "search");

/**
 * Switch between Search and Explore. Each view keeps its state (KeepAlive) and puts its own URL back.
 * @example setView("explore")
 */
function setView(name: View): void {
  view.value = name;
  close();
  error.value = "";
}
</script>

<template>
  <main>
    <h1><img src="/pokeball.svg" alt="" class="logo" />Pokédex Search</h1>
    <nav class="tabs">
      <button :class="{ on: view === 'search' }" @click="setView('search')">Search</button>
      <button :class="{ on: view === 'explore' }" @click="setView('explore')">Explore</button>
    </nav>
    <p v-if="error" class="error">{{ error }}</p>

    <!-- KeepAlive: switching tabs keeps each view's search, page, menus and chart -->
    <KeepAlive>
      <SearchView v-if="view === 'search'" />
      <ExploreView v-else />
    </KeepAlive>
  </main>
</template>

<style scoped>
main { max-width: 1100px; margin: 0 auto; padding: 16px; }
h1 { margin: 8px 0 12px; display: flex; align-items: center; gap: 10px; }
.logo { width: 1.4em; height: 1.4em; }
.tabs { display: flex; gap: 4px; margin-bottom: 12px; }
.tabs button.on { background: #2563eb; color: white; border-color: #2563eb; }
</style>
