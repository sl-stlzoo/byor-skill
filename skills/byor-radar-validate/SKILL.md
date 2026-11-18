---
name: byor-radar-validate
description: Checks a BYOR radar (radar-state.json, radar.csv or radar.json) for format errors and quality problems before publishing, such as missing columns, wrong ring or quadrant names, duplicate blip names, bad isNew values, unsafe HTML, empty or over-long descriptions, empty rings, and unbalanced quadrants, then explains and fixes each issue with the user. Use this skill whenever the user wants to validate, lint, check, sanity-test or debug a radar file, when BYOR shows a blank or broken radar, or as Phase 8 of the radar builder before export and publishing.
---

# BYOR Radar Validate

## Run the validator (preferred)
From the repo root, with files in the user's working directory:
```
python scripts/state_to_radar.py radar-state.json                 # (re)generate radar-output/radar.csv + radar.json
python scripts/validate_radar.py radar-output/radar.csv --state radar-state.json
python scripts/validate_radar.py radar-output/radar.csv --hosted   # only if publishing to radar.thoughtworks.com
```
Exit code 1 means errors. Warnings never block but should be reviewed with the user. Add `--json` for a
machine-readable report.

## No code execution? Manual checklist
Go through the generated CSV row by row:
1. Header is exactly `name,ring,quadrant,isNew,description` (optional `status` last).
2. Every row has all five fields; descriptions with commas are in double quotes; inner double quotes are doubled.
3. `ring` in {adopt, trial, assess, caution|hold} (case-insensitive) unless the radar is self-hosted with custom `RINGS`.
4. `quadrant` is one of the four chosen names (or the BYOR defaults when using the hosted site).
5. `isNew` is `TRUE` or `FALSE`.
6. No duplicate names; names are 40 characters or fewer.
7. Descriptions are 15-140 words, plain text or light HTML; no `<script>`, `<iframe>`, `<style>`.
8. No passwords, keys, tokens, prices under NDA or personal names.
9. At most 4 distinct quadrants and 4 distinct rings.
10. Counts: total under about 120; no quadrant over about 40; something in each quadrant.

## What the checks mean
| Finding | Level | Fix |
|---|---|---|
| Missing required column / empty name | error | repair header or fill name |
| `isNew` not TRUE/FALSE | error | normalise |
| Duplicate blip name | error | rename (e.g. "Microsoft Teams (chat)") or merge |
| Quadrant not a BYOR default name with `--hosted` | error | self-host or export with `--compat` |
| More than 4 quadrants or rings | error | merge |
| Forbidden HTML tag / credential-like text | error | remove |
| Ring not a default name (no `--state`) | warning | OK only if self-hosting with `RINGS` |
| Description empty/short/long | warning | rewrite via `byor-blip-assessor` |
| > 60% of blips in one ring / nothing in Adopt / nothing in Caution | warning | calibration question to the user |
| Domains still `pending` | warning | confirm skipped or finish interviews |

## Interaction pattern
1. Summarise in two lines: "N tools, M errors, K warnings."
2. Fix errors first, one at a time, with the smallest change that works; show before and after.
3. Group warnings by type; ask the user which to act on. Do not auto-rewrite descriptions without showing them.
4. Re-run until there are no errors. Record `progress.phase = 9` and the result in `progress.notes`.
