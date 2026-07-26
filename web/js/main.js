// Entry point. Owns two things and no view logic:
//   1. which loader runs when a tab is shown
//   2. the polling timers
//
// There are no `window`-assigned globals: every handler is wired with
// addEventListener (toolbar controls by id, dynamic rows by delegation), so the
// HTML and view templates carry no inline on* attributes to keep in sync.
import { $, api } from "./core.js";
import { S } from "./state.js";
import * as ui from "./ui.js";
import * as models from "./models.js";
import * as stats from "./stats.js";
import { loadDiscover } from "./discover.js";
import { loadWillRun } from "./willrun.js";
import { loadBuild } from "./build.js";
import { loadSetup } from "./setup.js";
import { loadContext } from "./context.js";
import { loadDocs } from "./help.js";
import { initWizard } from "./wizard.js";
import { initOnboarding } from "./onboarding.js";

/* ---------- tab loaders ---------- */
ui.onTabShown("build", loadBuild);
ui.onTabShown("setup", loadSetup);
ui.onTabShown("discover", loadDiscover);
ui.onTabShown("willrun", loadWillRun);
ui.onTabShown("stats", stats.loadStats);
ui.onTabShown("context", loadContext);
ui.onTabShown("help", loadDocs);

/* ---------- boot ---------- */
ui.initTabs();
ui.initModeToggle();
ui.initThemeControls();
ui.initSidebar();
ui.initDrawer();
ui.updatePageTitle();
initWizard();
initOnboarding();
models.initModels();
stats.initStats();

// deep-linkable tabs: #<tab> in the URL activates that tab (docs deep-links +
// tools/shoot.py). Runs after initTabs() has wired the click handlers.
window.addEventListener("hashchange", () => {
  const h = location.hash.slice(1);
  if (h) ui.switchTab(h);
});
if (location.hash) ui.switchTab(location.hash.slice(1));

function clock() {
  const el = $("#clock");
  if (el) el.textContent = new Date().toLocaleTimeString("en-GB") + " LOCAL";
}
clock();
setInterval(clock, 1000);

(async () => {
  S.SCHEMA = await api("/api/schema");
  await models.refresh();
  // theme/cvd defaults from config.json, used only when this device hasn't chosen
  try {
    const cfg = (S.STATE && S.STATE.config) || {};
    if (!localStorage.getItem("theme") && cfg.theme) ui.applyTheme(cfg.theme);
    if (localStorage.getItem("cvd") === null && cfg.cvd) ui.applyCvd(true);
    ui.applyMode(((S.STATE||{}).onboarding||{}).ui_mode || "lite");
  } catch (e) {}
})();

/* ---------- polls (idle unless their tab is showing) ---------- */
setInterval(() => { if (ui.activeTab() === "models") models.refresh(true); }, 4000);
setInterval(() => { if (ui.activeTab() === "stats") stats.loadStats(true); }, 4000);
setInterval(() => { if (ui.activeTab() === "models") models.refreshRouterLog(); }, 3000);
setInterval(() => { if (ui.activeTab() === "models") models.refreshVllmLog(); }, 3000);
models.refreshRouterLog();
models.refreshVllmLog();
