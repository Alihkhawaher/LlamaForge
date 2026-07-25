---
title: What's New
section: whats-new
order: 1
---

# What's New

This page summarizes the most recent additions to LlamaForge. Each entry links to the full reference for that capability. For the longer-term direction, see the project's `ROADMAP.md`.

## Lite and Advanced modes, with a guided first run

A first-run wizard now walks a new install through engine detection, hardware review, model selection, and a recommended tune — then applies it and loads the model. The dashboard runs in one of two modes: **Lite** presents a reduced, task-oriented set of controls; **Advanced** exposes every server flag. A hardware **auto-tune** proposes per-model settings (GPU-layer offload, KV-cache type, context ceiling, and intent presets for balanced / speed / context / coding) sized to the detected VRAM.

See [First Run](first-run.md) and [Models & Tuning](models.md).

## Anthropic-compatible endpoint

The panel exposes an Anthropic-compatible `POST /v1/messages` endpoint that translates to the local OpenAI-style router, with full streaming and tool-use support. Combined with the existing OpenAI-compatible surface, LlamaForge can serve clients written for either API against your local models.

See [HTTP API](api.md).

## One-click agent setup

A **Connect an Agent** panel generates — and optionally writes — the configuration for **Claude Code**, **Codex**, and **pi.dev**, pointing each at your local endpoint. Claude Code is scoped to `127.0.0.1`; generated files are backed up before any change is written.

See [Connect an Agent](agents.md).

## Context Wiki

A working directory of Markdown context documents, composed into named **profiles** and selected **per model**. An active profile is delivered two ways: injected into requests through the Anthropic shim and the OpenAI proxy, or exported into an agent's native context file (`CLAUDE.md` / `AGENTS.md`) inside a managed marker region. Because the injected prefix is stable, the router's prompt-cache reuses it across requests.

See [Context Wiki](context-wiki.md).

## Light and dark themes, plus a colorblind-safe mode

The dashboard now offers a **Light** theme alongside the original dark one, and an independent **Colorblind-safe** mode that applies a universal Okabe–Ito status palette and adds non-color cues (glyphs and labels) so status never depends on hue alone. The two axes are orthogonal — all four combinations are valid — and each choice persists per device.

See [Theming & Accessibility](theming.md).

## In-app documentation

The documentation you are reading is available inside the dashboard under the **Help** view and is also published as a static site. Both surfaces render from a single Markdown source, so they never drift.

## A collapsible sidebar layout

Navigation moved from a top tab bar to a left **sidebar** that collapses between a compact icon rail and a labeled, expanded state. Settings are pinned at the bottom; the layout adapts to narrow windows with an overlay drawer. All existing navigation, theming, and keyboard shortcuts are unchanged.

See [Keyboard Shortcuts](keymap.md).
