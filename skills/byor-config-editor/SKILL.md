---
name: byor-config-editor
description: Lets the user add, remove, rename, reorder or re-map software domains, quadrant schemes, ring definitions, seed tools and interview questions for the BYOR radar builder, either for one session or permanently via config.local overrides or a fork. Use this skill whenever the user says add a domain, remove a category, rename quadrants, change the starting list of software areas, customise the questions, use my own categories, or fork or edit the radar skills repo configuration.
---

# BYOR Config Editor

All behaviour is driven by `config/*.yaml`. Three ways to change it, from lightest to heaviest:

1. **Session change** (default): change the in-memory domain/quadrant list and record the change in
   `radar-state.json` (`domains`, `quadrants`). Nothing outside the user's working directory changes.
2. **Local overrides**: create `config.local/` beside the working directory with only the changed files or entries.
   Merge rules: files with the same name override top-level keys; `domains` merge by `id` (an entry with
   `disabled: true` removes a domain); `seeds` and `probes` lists replace, not append, unless the key ends with `_add`.
3. **Fork**: the user forks the repo, edits `config/`, and gives the builder their fork URL as the new base. Remind them
   to run `python scripts/check_config.py`.

## Common edits

**Add a domain (quick-add, ask one at a time):** name, quadrant, one-sentence scope, two probing questions, optional
seeds, optional lens. Generate the `id` as a lowercase slug. Example entry:
```yaml
- id: fleet-management
  name: Fleet Management
  quadrant: business-ops
  scope: "Vehicles, drivers, maintenance, fuel and telematics."
  probes: ["How many vehicles and who maintains them?", "Which telematics or fuel cards are in use?"]
  seeds: [Samsara, Geotab]
  lens: [safety compliance, maintenance cost, data ownership]
```
**Remove or skip a domain:** session: set `status: skipped` with a reason. Permanent: `disabled: true` in
`config.local/domains.yaml` or delete in a fork.
**Rename a domain or quadrant:** change `name` only; never change `id` after state exists.
**Move a domain between quadrants:** change `quadrant`; blips follow their domain.
**Custom quadrant scheme:** exactly four quadrants with unique ids and names, no commas in names, each with a short blurb.
Set `quadrant_scheme: custom` and list them under `schemes.custom.quadrants`.
**Change a ring's wording or criteria:** edit `config/rings.yaml` (permanent default) or do it in Phase 4 (per radar).
**Change depth, limits or evidence behaviour:** edit `config/settings.yaml`.
**Add seeds:** alphabetical, mark open source `(FOSS)` or `(OSS-core)`. Seeds are recall prompts, never endorsements.
Do not add anything marketing-like.

## After editing
- If PyYAML is available run `python scripts/check_config.py`. Otherwise re-read the files for: unique ids, every
  domain's quadrant exists, exactly four quadrants, seeds as a flat list, no tabs in YAML.
- Show the user a compact diff and confirm. Do not rewrite untouched parts of a file.
- If a radar is already in progress, ask whether to apply the change to it (state) or only to future radars.

## Constraints to remind users about
- BYOR draws exactly 4 quadrants and up to 4 rings.
- More than about 120 blips is hard to read; many domains means fewer blips per domain.
- Custom quadrant names require self-hosting BYOR or `--compat` export (see `byor-radar-publish`).
