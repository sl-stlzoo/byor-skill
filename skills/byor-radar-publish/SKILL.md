---
name: byor-radar-publish
description: Exports a finished radar to BYOR-ready CSV/JSON, publishes the single-page static site, (including hosted-site compatibility mode and custom quadrant/ring names for self-hosting), helps the user choose and complete a hosting route (public Google Sheet, GitHub raw CSV, local Docker, self-hosted BYOR), explains privacy trade-offs, and produces a shareable summary. Use this skill whenever the user wants to export, publish, host, share, load, view or open their radar in BYOR, asks how to get a radar URL, or reaches Phase 9 of the radar builder.
---

# BYOR Radar Publish

Precondition: Phase 8 passed (no validator errors). Reference: `references/hosting-options.md` and
`byor-radar-builder/references/byor-format.md`. If you can browse, re-check the upstream README for changes first.

## Step 0: Publishing gate and redaction (always)
State in two lines what will be shared and who can see it; ask for confirmation. Offer a redaction pass (owner names, dates,
incident references, any blip a security owner would not want exposed) before exporting. Rules: `byor-radar-builder/references/security-guardrails.md`.

## Step 1: Choose the audience and privacy level (tappable)
"Who should be able to see this radar?"
- Just me / my team (private)
- Anyone in my organisation
- Anyone with the link (public)
Remind: the radar lists tools, gaps and risks. Public hosting is irreversible once copied.

## Step 2: Choose the hosting route (recommend by answer)
| Route | Privacy | Custom quadrant names | Effort |
|---|---|---|---|
| A. Local Docker with mounted files | private (your machine/network) | yes | one command |
| B. Self-hosted BYOR (internal server, container platform) | private to your network | yes | moderate |
| C. Hosted site + public Google Sheet | public to anyone with the link | no (use compat) | easy |
| D. Hosted site + raw CSV on a public GitHub repo | public | no (use compat) | easy |
| E. Hosted site + private Google Sheet | private to Google accounts you share with | no (use compat) | needs sign-in |

Default recommendations: private audience -> A or B; public sharing and no Docker -> C with compat; classic
quadrants (Techniques/Platforms/Tools/Languages & Frameworks) -> any route works with no compat.

## Step 3: Export
```
python scripts/state_to_radar.py radar-state.json                  # custom names, for A/B
python scripts/state_to_radar.py radar-state.json --compat         # hosted site (C/D/E)
python scripts/state_to_radar.py radar-state.json --hold-label Caution   # optional rename of the 4th ring
python scripts/state_to_radar.py radar-state.json --print-env      # RINGS / QUADRANTS for self-hosting
python scripts/validate_radar.py radar-output/radar.csv [--hosted]
```
Add `--full` only for an internal data file (it adds domain, owner, confidence, last_reviewed columns; BYOR ignores them).
No code execution: print the CSV in a code block, built from state, and give the `RINGS`/`QUADRANTS` JSON strings by hand.

## Step 4: Walk through the chosen route
Give numbered steps, one at a time, confirming each. Details and commands are in `references/hosting-options.md`.
Always finish with the exact text to paste into BYOR's "Build my radar" box and what the user should see
(four quadrants labelled with their names, blips coloured by ring, a list of blips per ring on the side).

## Step 5: Confirm it works
Ask what they see. If blank or malformed, go to the troubleshooting table in the hosting reference. Re-run
`byor-radar-validate` if needed.

## Step 3b: Host the single-page site
`radar-output/index.html` is one self-contained file. Options: open locally; GitHub Pages (public repo or Pages on a private repo per plan); Netlify/Cloudflare Pages/S3+CDN; an internal web server or intranet; attach to an email. For private audiences use access-controlled hosting (SSO-protected static host or intranet) because the page embeds every blip and the CSV. `noindex` is the default; `--public` only on explicit request.

## Step 6: Deliver extras
- `radar-output/radar-summary.md` built from `templates/radar-summary.md` (headlines, by-quadrant tables, decisions,
  gaps, maintenance). Fill from state; keep facts only.
- A one-paragraph "how we update this" note: edit `radar-state.json`, re-export, reload.
- Set `progress.phase = 10` and continue to Maintain.

## Guardrails
- Never publish on the user's behalf (no creating public sheets or repos) unless they explicitly ask and a tool allows it.
- Never include credentials or private IDs in outputs.
- If the user chose private hosting but then asks for a public link, restate the privacy trade-off once.
