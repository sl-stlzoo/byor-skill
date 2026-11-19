# byor-skill

Conversational **agent skills** that guide anyone, one question at a time, through building their own technology radar with
Thoughtworks' open source [Build Your Own Radar (BYOR)](https://www.thoughtworks.com/radar/byor), and, optionally, through
contributing to a **consortium benchmark** with peer organisations. Everything runs offline from files; there is no server, account or telemetry.

| You are | You get |
|---|---|
| **An organisation building its radar** | A guided or batch interview over a configurable list of software domains; `radar.csv` / `radar.json` for BYOR; a **single-page static website** with an interactive radar, ring guide, themes, blips, actions and FAQ |
| **A consortium member** | A share-safe `contribution.json` (tools, rings, evidence buckets; never descriptions, owners or incidents), named by default or anonymous, with a preview and consent step |
| **A consortium convener** | Intake and privacy-preserving aggregation (minimum 3 organisations), a **benchmark website** for everyone and a private **"you vs the round" report** for each member |

Both interview paths include [36 starter software areas](config/domains.yaml), from accounting and purchasing to
admissions, fundraising, education, facilities, HR, retail, and food and beverage. The cash-counting section
lets you record that you operate fully cashless or that payment practices vary by site.

## Start here
| Goal | Read |
|---|---|
| Evaluate it for your organisation | [SECURITY.md](SECURITY.md): security model, threats, controls, fixes, how to verify and pin |
| Deploy the repo and test it in your AI client | [RUNBOOK.md](RUNBOOK.md) then [TESTING.md](TESTING.md) |
| Update your radar next half-year | Start a chat with the same link and say "update my radar"; bring `radar-state.json` and `editions/` |
| Understand consortium benchmarks, the benchmark site and member reports | [docs/CONSORTIUM.md](docs/CONSORTIUM.md) |
| Run a round | [docs/consortium-charter-template.md](docs/consortium-charter-template.md) and `skills/byor-radar-convene/` |
| Prompts to paste into an AI assistant | [BOOTSTRAP_PROMPT.md](BOOTSTRAP_PROMPT.md) |
| Change over time: editions (built), round trends (built), panel analysis (planned) | [docs/ROADMAP-TIME.md](docs/ROADMAP-TIME.md) |

## Use it: one prompt
**Prefer to answer in one sitting?** Open the [project site](https://sl-stlzoo.github.io/byor-skill/) and
choose **Batch Interview**. Fill in the worksheet or import the [blank CSV template](templates/byor-blank.csv)
after completing it. Copy the JSON prompt into a new chat, or attach your completed spreadsheet with the
[batch start prompt](BOOTSTRAP_PROMPT.md#byor-interview-batch-start). The worksheet does not upload data or
save drafts. Interview notes go into the JSON; the CSV export includes only the five Thoughtworks blip fields.

**Prefer a conversation?**
Paste into any capable AI assistant (the repo owner and name are filled in by `scripts/set_owner.py`; shown here as placeholders):
```
Use https://github.com/sl-stlzoo/byor-skill to guide me, one question at a time, through building my own
Thoughtworks BYOR radar. Start by reading AGENTS.md in that repo and follow it exactly.
```
Most reliable in the Claude app: attach the repo zip with code execution on and say "Unzip this, read AGENTS.md, and guide me through building my radar." Variants (raw link, single-file bundle, resume, fork, next edition, consortium): [BOOTSTRAP_PROMPT.md](BOOTSTRAP_PROMPT.md).

## The guided workflow
| Phase | What happens | Skill |
|---|---|---|
| 0 Welcome | Explains BYOR; you pick depth (quick, standard, deep) and whether the agent may check facts on the web | builder |
| 1 Context | Organisation, audience, decision to support, owner, what "new" means | builder |
| 2 Domain scope | Keep, skip, rename or add domains; clarify ambiguous ones (for example ticketing) | builder, config-editor |
| 3 Quadrants | Choose a scheme (business domains, Thoughtworks classic, or your own) and map domains to 4 quadrants | builder |
| 4 Rings | Tailor Adopt, Trial, Assess, Caution to your organisation, one ring at a time | blip-assessor |
| 5 Interviews | Per quadrant, per domain: discover tools in use, piloted, evaluated, retiring; rate each; write the blip | domain-interview, blip-assessor |
| 6 Calibration | Review each ring across all quadrants; overlaps and gaps | builder |
| 7 Narrative and site | Edition, tagline, intro, 3-4 themes, actions, contributors; builds `index.html` | radar-site |
| 8 Validate | Lint format and quality | radar-validate |
| 9 Publish | Export; host the site; load data into BYOR | radar-publish |
| 10 Maintain | Save this edition (half-yearly), set the next review | builder |
| Next time | **Update**: only what changed, about 25 minutes; the site gets a "What changed" section and per-tool history | update |
| 11 Contribute (optional) | Share a redacted contribution with a consortium round | radar-share |

The method follows the canonical Thoughtworks radar ([FAQ](https://www.thoughtworks.com/radar/faq)): an opinionated snapshot of experience, not a survey; Trial needs real use; Adopt is a high bar; Caution reflects a negative experience; themes tell the story. Details: `skills/byor-radar-builder/references/canonical-radar-principles.md`. This project is independent and not affiliated with Thoughtworks.

## Deploy
Short version (full steps in [RUNBOOK.md](RUNBOOK.md)):
```
python scripts/set_owner.py sl-stlzoo YOUR_REPO_NAME [branch-tag-or-commit-sha]   # parameterises owner, repo name, ref everywhere
bash scripts/audit.sh && pytest -q tests                                                 # security self-audit and tests
git push; enable Pages (main, /root); python scripts/verify_deploy.py                    # landing page + deploy check
```
Rename later by re-running `set_owner.py`; the single source of truth is `project.json`. Pin a reviewed commit SHA for production use.

## Scripts (standard library for radar generation; rebuilding the browser question bank requires PyYAML)
```
# Radar
python scripts/state_to_radar.py radar-state.json [--compat] [--full] [--hold-label Hold] [--print-env]
python scripts/validate_radar.py radar-output/radar.csv [--state radar-state.json] [--hosted] [--json]
python scripts/build_site.py radar-state.json [--theme radar-theme.json] [--public] # -> radar-output/index.html
python scripts/build_interview.py                                                  # regenerate the public question bank
python scripts/radar_stats.py radar-state.json
python scripts/freeze_edition.py radar-state.json                                  # save this edition, mark what changed (keeps newest 4)
python scripts/compare_editions.py radar-state.json                                # what changed since the last edition
python scripts/lint_plain.py                                                       # plain-language lint for skill wording
bash   scripts/serve_local.sh radar-state.json 8080                                 # BYOR in Docker, localhost only
# Consortium: member
python scripts/registry.py match radar-state.json
python scripts/state_to_contribution.py radar-state.json --kit round-kit.json --profile share-profile.json [--preview]
python scripts/validate_contribution.py contribution.json --kit round-kit.json
# Consortium: convener
python scripts/aggregate_round.py --kit round-kit.json --inbox inbox --roster roster.json --out round-output
python scripts/compare_rounds.py old/aggregate.json round-output/aggregate.json --out round-output   # round 2+: trends
python scripts/refresh_share_profile.py radar-state.json --kit round-kit.json --previous-profile share-profile.json   # member, round 2+
python scripts/build_benchmark.py site round-output/aggregate.json --narrative narrative.json
python scripts/build_benchmark.py members round-output/aggregate.json --inbox inbox --kit round-kit.json
# Maintainers
python scripts/set_owner.py ...  |  python scripts/build_bundle.py  |  python scripts/verify_deploy.py  |  bash scripts/audit.sh  |  python scripts/check_config.py
```
Agents without code execution fall back to chat snapshots and manual checklists (the consortium steps and the site need the scripts).

## Customise
In a generated radar, open **Theme** to preview an accent, four quadrant colours and a light or dark
appearance. Download the branded HTML to keep or share, or download `radar-theme.json` and pass it to
`build_site.py --theme` to reuse your branding next edition. The default red and neutral design is inspired
by [AZA Technology](https://aza-technology.github.io/); the sites do not load its assets.

After editing the starter domain, ring or quadrant configuration, run `python scripts/build_interview.py` and
commit the regenerated question bank with your config changes. The public worksheet uses `config/` only, not
`config.local/`. To test the page locally, run `python -m http.server 8000 --bind 127.0.0.1` from the repo root
and open `http://127.0.0.1:8000/interview.html`.
- **Domains:** `config/domains.yaml` (id, name, quadrant, scope, probes, seeds, lens), or tell the agent "add a domain called fleet management".
- **Quadrants and rings:** `config/quadrants.yaml` (BYOR draws exactly 4 quadrants), `config/rings.yaml`; Phase 4 tailors rings per radar.
- **Depth, limits, evidence mode, site settings:** `config/settings.yaml`.
- **Tool registry and vocabularies for consortium rounds:** `config/tools.json` (`scripts/registry.py add`), `config/consortium-vocab.json`.
- After editing: `python scripts/check_config.py`, `pytest -q tests`, `python scripts/build_bundle.py`.

## Important facts about BYOR (verified against the upstream README, Nov 2026)
- Data fields: `name, ring, quadrant, isNew, description` (optional `status`: New / Moved In / Moved Out / No Change).
- The hosted site accepts only default ring and quadrant names; custom quadrant names need a self-hosted BYOR (`RINGS` and `QUADRANTS` environment variables) or this repo's `--compat` export.
- The fourth ring is now **Caution**; `hold` (any case) is still accepted.
- Re-check upstream before publishing: https://github.com/thoughtworks/build-your-own-radar

## Quality and limits
Seed tool lists are recall prompts dated Nov 2026, alphabetical, not endorsements, and possibly stale. The behavioural evals in `evals/` (33 scenarios) are meant to be run against a real AI client and have not been run for you. Consortium results are informal opinions, and the convener always sees raw contributions.

## License
MIT for this repository. BYOR is AGPL-3.0 and is not included here.
