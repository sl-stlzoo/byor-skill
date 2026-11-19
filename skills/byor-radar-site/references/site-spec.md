# Single-page site spec (what `scripts/build_site.py` produces)

One self-contained `index.html` (about 40-100 KB). No external requests, fonts, images or scripts. Works offline.

## Section order (mirrors the canonical radar page)
1. **Top bar** (sticky): org name, anchors, theme toggle
2. **Hero:** edition label and month, title, tagline, intro, counts per ring + New + Moved, buttons (Explore, CSV, JSON, Print)
3. **The radar:** SVG, four quadrants and rings, numbered blips (shape = status), quadrant tabs (zoom), ring chips, search, legend
4. **How to read:** ring cards (canonical meaning + the user's tailored criteria) and the "keeping up" reading order
5. **Themes for this edition:** titled essays with linked blips
6. **All blips:** cards grouped quadrant then ring: number, ring, status, domain, description, owner, last reviewed
7. **Decisions and actions** table (if provided)
8. **FAQ:** `<details>` accordions
9. **About:** contributors, data downloads, BYOR link, next review
10. **Footer:** attribution and non-affiliation note

## Data it reads (radar-state.json)
`meta`: organization, radar_title|site_title, edition, published, tagline, intro, hold_label, contributors[], how_to_nominate, cadence, next_review, owner.
`quadrants[]`, `rings[]` (+ `criteria`), `domains{}`, `blips[]` (+ `status`, `isNew`, `radial`, `owner`, `last_reviewed`), `themes[]`, `actions[]`.

## Behaviours
- Radial position from `radial` (0 inner edge to 1 outer edge of the ring); else a stable pseudo-random spot. Angle is arbitrary.
- Shapes: triangle = new, diamond = moved ring, circle = no change.
- Blips are real links to their card (works without JS). JS adds filtering, quadrant zoom (auto on narrow screens), hover highlight, theme toggle.
- Accessible: skip link, landmarks, keyboard focus styles, text alternative (all blips listed), colour is never the only cue (labels, numbers, shapes), reduced-motion respected.
- Print: controls hidden, FAQ expanded, cards not split.
- Privacy: `noindex` by default.
- CSV/JSON are embedded as data URIs and use the user's quadrant and ring names (self-hosted BYOR). For the hosted BYOR site use `state_to_radar.py --compat`.

## Customising
Open **Theme** in the generated radar to preview the appearance, accent and four quadrant colours. **Download
Branded HTML** saves those settings in a new self-contained page. **Download Theme Settings** saves a JSON
object with `mode` (`system`, `light`, or `dark`), `accent`, and `q0`–`q3` (six-digit hex colours in radar
quadrant order). Pass it to `scripts/build_site.py` with `--theme radar-theme.json` when building another edition.
An explicit `--accent` overrides only the accent from that file.
