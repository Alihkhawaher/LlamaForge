---
title: Theming & Accessibility
section: guides
order: 9
---

# Theming & Accessibility

Light/dark appearance and a colorblind-safe mode, both persisted per browser and applied before first paint so the dashboard never flashes the wrong theme.

## What it does

All colors in the dashboard are CSS custom properties defined on `:root` in `web/index.html`. The dark palette (the default) is the base `:root` block; `:root[data-theme="light"]` overrides it with a light set of the same variable names, so every component that already uses `var(--ink)`, `var(--panel)`, etc. repaints correctly with no per-component changes. Switching theme also toggles a couple of dark-mode-only effects off in light mode: the CRT scanline overlay (`body::after`) and the glow/box-shadow on the pulse indicator and lit meter segments.

A separate, independent attribute, `data-cvd="safe"`, layers a colorblind-safe palette on top of whichever theme is active. `:root[data-cvd="safe"]` overrides the status-color tokens with the Okabe–Ito palette:

| Token | Default | CVD-safe (Okabe–Ito) |
|---|---|---|
| `--green` (ok/success) | `#39d98a` | `#009E73` (bluish green) |
| `--red` (error/hot) | `#ff5c57` | `#D55E00` (vermillion) |
| `--amber` (accent/status) | `#ffb000` | `#E69F00` (orange) |
| `--cyan` (info) | `#3fd7e6` | `#56B4E9` (sky blue) |

CVD-safe mode doesn't stop at recoloring — it also adds cues that don't depend on hue at all, since a palette swap alone still relies on the viewer telling colors apart:

- `.msg.ok`, `.msg.err`, `.msg.work`, and `#toast.ok`/`#toast.err` get a `::before` content glyph: `✓` (U+2713) for ok, `✗` (U+2717) for error, `…` (U+2026) for in-progress.
- `.pulse` (the "live" status dot) gets a `::after` label reading `LIVE`.
- `.seg.hot` (an overloaded/hot meter segment) gets a `::after` `!` glyph.

Both settings are controlled from `web/app.js`: `applyTheme(t)` sets `data-theme` to `"light"` or `"dark"` (anything else falls back to dark) and syncs the toggle buttons' active state; `applyCvd(on)` sets or removes `data-cvd="safe"` and syncs the checkbox. `setTheme()`/`setCvd()` wrap those with persistence: they call `applyTheme`/`applyCvd` immediately, write the choice to `localStorage` (`theme`, `cvd`), and push it to the backend via `POST /api/config` so it becomes that device's server-side default too.

Resolution order, most specific first:

1. **`localStorage`** — this browser's own explicit choice, if it has ever set one.
2. **Server config** (`cfg.theme` / `cfg.cvd`, read from `/api/state` on `refresh()`) — applied only when this browser's `localStorage` has no entry yet, so it acts as a fallback default rather than an override.
3. **OS preference** — a small inline script in `<head>`, which runs before the stylesheet paints and before `app.js` loads, checks `localStorage.getItem("theme")` first and otherwise falls back to `window.matchMedia("(prefers-color-scheme: light)")`. This same script also applies `data-cvd="safe"` immediately if `localStorage.getItem("cvd")==="1"`. Because it runs synchronously in `<head>` before any content renders, there is no flash of the wrong theme on load.

## How to use it

1. Open the theme toggle (**Light** / **Dark** buttons) anywhere it appears in the header — click one to switch immediately.
2. Toggle the colorblind-safe checkbox to switch the status palette to Okabe–Ito colors and enable the non-color status cues, independent of the light/dark choice.
3. Your choice is remembered on this device via `localStorage`, and also saved to LlamaForge's config so a fresh browser profile on the same machine picks it up as the default.

## Key options / reference

| Concept | Source | Behavior |
|---|---|---|
| Dark palette (default) | `web/index.html` `:root{...}` | Base CSS custom properties for all colors, fonts, and surfaces. |
| Light palette | `web/index.html` `:root[data-theme="light"]{...}` | Overrides the same variable names; also disables scanlines and glow effects. |
| Colorblind-safe palette | `web/index.html` `:root[data-cvd="safe"]{...}` | Overrides `--green`/`--red`/`--amber`/`--cyan` (and related border/tint tokens) with Okabe–Ito hex values. |
| Non-color status cues | `web/index.html` `:root[data-cvd="safe"] .msg.*::before` etc. | Adds `✓`/`✗`/`…` glyphs, a `LIVE` label, and a `!` glyph so status doesn't rely on hue alone. |
| Apply theme | `web/app.js` `applyTheme(t)` | Sets `data-theme`, syncs toggle button active state. |
| Apply CVD | `web/app.js` `applyCvd(on)` | Sets/removes `data-cvd="safe"`, syncs the checkbox. |
| Persist theme | `web/app.js` `setTheme(t)` | `applyTheme` + `localStorage.setItem("theme", t)` + `POST /api/config`. |
| Persist CVD | `web/app.js` `setCvd(on)` | `applyCvd` + `localStorage.setItem("cvd", ...)` + `POST /api/config`. |
| No-flash resolver | `web/index.html` inline `<head>` script | Runs before paint: `localStorage` theme/cvd, else OS `prefers-color-scheme`. |
| Config fallback | `web/app.js` `refresh()` | Applies server `cfg.theme`/`cfg.cvd` only when this browser's `localStorage` has no entry yet. |

## Troubleshooting

If a new browser profile on the same machine doesn't pick up the theme you set elsewhere, that's expected the first time — `localStorage` is per-browser, and the server-side config value only becomes the applied default on the next `refresh()`, and only if that browser hasn't already chosen its own theme. If a previously-set theme seems "stuck" after changing the server default, clear the `theme`/`cvd` keys from that browser's `localStorage`, since a local choice always wins over the config fallback.

See also [Context Wiki](context-wiki.md) and [Connect an Agent](agents.md) for the other panels this appearance system applies to.
