// Help tab: the docs corpus, rendered server-side from the same Markdown that
// builds the published site.
import { $, $$, esc, setHTML, api } from "./core.js";

let DOCS = null;

export async function loadDocs() {
  if (DOCS) return;
  DOCS = await api("/api/docs");
  const nav = $("#docs-toc-nav");
  setHTML(nav, DOCS.sections.map(s =>
    `<div class="sec">${esc(s.title)}</div>` +
    s.pages.map(p => `<a href="#" data-slug="${esc(p.slug)}">${esc(p.title)}</a>`).join("")
  ).join(""));
  $$("a[data-slug]", nav).forEach(a =>
    a.onclick = e => { e.preventDefault(); openDoc(a.dataset.slug); });
  $("#docs-search").oninput = e => filterDocs(e.target.value.toLowerCase());
  if (DOCS.sections[0] && DOCS.sections[0].pages[0]) openDoc(DOCS.sections[0].pages[0].slug);
}

async function openDoc(slug) {
  const pg = await api("/api/docs/page?slug=" + encodeURIComponent(slug));
  if (!pg || pg.error) return;
  setHTML($("#docs-body"), pg.html);                // trusted local renderer output
  setHTML($("#docs-page-toc"), (pg.toc || [])
    .map(t => `<a href="#${esc(t.id)}" style="padding-left:${(t.level-1)*8}px">${esc(t.text)}</a>`).join(""));
  $$("#docs-toc-nav a").forEach(a => a.classList.toggle("active", a.dataset.slug === slug));
  $("#docs-body").scrollTop = 0;
}

function filterDocs(q) {
  const hits = new Set(DOCS.search
    .filter(p => p.title.toLowerCase().includes(q) ||
                 p.headings.some(h => h.toLowerCase().includes(q)))
    .map(p => p.slug));
  $$("#docs-toc-nav a[data-slug]").forEach(a =>
    a.style.display = (!q || hits.has(a.dataset.slug)) ? "" : "none");
}
