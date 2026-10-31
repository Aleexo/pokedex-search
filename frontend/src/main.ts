import { createApp } from "vue";
import "./style.css"; // shared styles first, so each component's own styles come after
import App from "./App.vue";

createApp(App).mount("#app");
