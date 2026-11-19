---
name: byor-radar-site
description: Runs the narrative workshop for a finished radar (edition label, tagline, intro, 3-4 themes, contributors, nomination process, decisions and actions) and generates the user's excellent single-page static website (index.html) in the structure of the canonical Thoughtworks Technology Radar, with an interactive radar, ring guide, themes, all blips, FAQ and CSV/JSON downloads. Use this skill whenever the user wants a website, web page, report, summary, narrative, themes, "the story of the radar", something to share or present, or reaches Phase 7 of the radar builder, even if they never say "static site".
---

# BYOR Radar Site

Turns the data and the user's answers into the same shape a canonical radar page has: edition and date, title and
tagline, intro, the radar, ring guide, **themes**, all blips, actions, FAQ, contributors. Principles and source rationale:
`byor-radar-builder/references/canonical-radar-principles.md`. Wording and probes: `references/narrative-playbook.md`.
Site structure and customisation: `references/site-spec.md`.

## Preconditions
Phase 6 (calibration) done; blips saved in state. If fewer than 8 blips, warn that themes will be thin.

## Narrative workshop (one question per message in guided chat)

1. **Edition and tagline.** Offer 3 tagline options in the canonical spirit ("An opinionated guide to ...") built from
   `meta.purpose`; the user picks or edits. Edition label (default `Edition 1`) and publication month.
2. **Intro.** Draft 2-3 sentences: what the radar is, whose experience it reflects, what it is not (not a survey, not an
   approved list, not vendor-influenced). Show it; accept edits. Save `meta.intro`.
3. **Themes (the heart).** Target `site.themes_target` (3 by default, up to 4):
   a. Propose 3-5 candidate patterns *from the data and the interviews*, each as one sentence (e.g. overlapping tools,
      open source momentum, security coverage gaps, AI governance, shadow IT, vendor consolidation, contract renewals).
      Tappable multi-select, plus "something else".
   b. For each chosen pattern, ask one probing question that only the user can answer ("What surprised you most about
      the overlap?", "What do you expect to happen before the next review?").
   c. Draft the theme using the pattern in `canonical-radar-principles.md`: 90-180 words, 2-4 linked blips written as
      `[[Exact Blip Name]]`, one nuance, one caution if relevant, one forward-looking sentence. Use only facts from state
      and the user's answers. Show it, accept edits, save to `state.themes[]` as `{title, body:[paragraphs]}`.
4. **Decisions and actions.** From Caution/Trial/Assess blips propose actions (action, tool, owner, by when); user edits.
   Save `state.actions[]`.
5. **People and process.** Contributors (names or roles, as the user wishes; offer "team only"), how colleagues can nominate
   a tool, cadence and next review. Save `meta.contributors`, `meta.how_to_nominate`, `meta.cadence`, `meta.next_review`.
6. **Look and privacy.** Use the default red and neutral theme unless the user asks for other colours, and ask whether the page may be indexed by search engines
   (default no) and whether contributors' names may appear publicly.
7. **Confirm** in one compact recap (title, tagline, themes list, action count) before building.

## Build
```
python scripts/build_site.py radar-state.json                      # -> radar-output/index.html
python scripts/build_site.py radar-state.json --accent "#1d4ed8"   # custom accent
python scripts/build_site.py radar-state.json --theme radar-theme.json  # reuse saved branding
python scripts/build_site.py radar-state.json --public             # allow search indexing (only if user chose)
```
Read the printed WARNINGS (missing themes, unknown `[[links]]`, no contributors) and fix them with the user.
If you cannot run code, hand-write the page using the section order and rules in `references/site-spec.md` as one
self-contained HTML file, or offer the CSV plus the themes as Markdown.

## Deliver
Present `radar-output/index.html` (and `radar.csv`, `radar.json`, `radar-summary.md`). Tell the user in three lines: how to open
it (double-click), how to host it (any static host, see `byor-radar-publish`), and that it contains the whole radar
so access control matters.
The generated page's **Theme** link opens an offline editor. The user can preview colours, download a branded
HTML copy, or save settings for the next edition.

## Quality bar (check before presenting)
- Intro says opinion, not survey, not approved list.
- Every theme links at least two real blips and none invents facts.
- Rings explained in the user's words (Phase 4 criteria) and in the canonical reading order.
- Works with no JavaScript, on a phone, in dark mode and in print (the generator does; verify warnings).
- No credentials, prices under NDA, or personal names the user did not approve.
- The footer keeps the attribution: method adapted from the Thoughtworks Technology Radar, not affiliated. Do not use
  Thoughtworks logos, colours or text, and do not imply endorsement.
