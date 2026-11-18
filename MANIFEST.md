# Manifest

Every file in the repository and what it is for. Generated files are marked (gen).

## Entry points and project files
| Path | Purpose |
|---|---|
| `AGENTS.md` | Agent entry point: load order, security rules, file map, absolute URL block (written by `set_owner.py`) |
| `CLAUDE.md` | One line pointing Claude clients to `AGENTS.md` |
| `README.md` | Overview, workflow, scripts, customisation |
| `BOOTSTRAP_PROMPT.md` | Copy-paste prompts (standard, Pages, raw, bundle, zip, resume, fork, next edition) |
| `index.html` | GitHub Pages landing page; fills in owner/repo for the copy-paste prompt |
| `BUNDLE.md` (gen) | CORE single-file bundle (about 100 KB): everything for one organisation's radar and site except scripts, examples and consortium material |
| `BUNDLE-FULL.md` (gen) | Everything in one file (scripts, consortium, docs, examples); large, prefer the zip |
| `project.json` | Single source of truth: owner, repo name, ref, site credit; managed by `set_owner.py` |
| `RUNBOOK.md` | Deploy, verify, evaluate in the Claude app, rename, troubleshoot |
| `SECURITY.md` | Security model, threats (OWASP LLM mapping), controls, issues fixed, verification, enterprise guidance, reporting |
| `TESTING.md` | Tested-clients table, tiers, scripted protocol, checks A-I |
| `LICENSE`, `.gitignore`, `.nojekyll`, `.github/workflows/validate.yml` | MIT licence; keeps radar data out of git; Pages passthrough; CI (audit, tests, bundle freshness) |

## Config (edit to customise)
| Path | Purpose |
|---|---|
| `config/domains.yaml` | The 25 starter software domains with probes, seed tools, rating lenses |
| `config/quadrants.yaml` | Quadrant schemes and default domain mapping |
| `config/rings.yaml` | Adopt / Trial / Assess / Caution meanings and criteria (canonical wording, paraphrased) |
| `config/settings.yaml` | Depth profiles, soft limits, evidence mode, site and UI settings |
| `config/tools.json` | Canonical tool registry (214 tools, ids, aliases) for consortium rounds |
| `config/consortium-vocab.json` | Closed vocabularies for contributions (sectors, bands, regions, buckets, caution tags, limits) |

## Skills (each folder is a self-contained `SKILL.md`)
| Path | Purpose |
|---|---|
| `skills/byor-radar-builder/` | Orchestrator: 12-phase workflow, quadrant loop, guarantees |
| `.../references/workflow.md` | Scripted wording for phases 0, 1, 3, 6, 10 |
| `.../references/byor-format.md` | Verified BYOR facts: formats, names, Docker, env vars |
| `.../references/canonical-radar-principles.md` | The Thoughtworks method and how this repo honours it |
| `.../references/security-guardrails.md` | Binding agent security rules |
| `.../references/state-schema.md` | `radar-state.json` structure and update rules |
| `.../references/conversation-style.md`, `error-recovery.md` | Message style and failure handling |
| `skills/byor-domain-interview/` (+ `interview-playbook.md`) | One-domain discovery interview |
| `skills/byor-blip-assessor/` (+ `ring-rubric.md`, `blip-writing.md`) | Ring tailoring, rating rubric, description writing |
| `skills/byor-radar-site/` (+ `narrative-playbook.md`, `site-spec.md`) | Narrative workshop and single-page site |
| `skills/byor-radar-validate/` | Lint radar files, manual checklist |
| `skills/byor-radar-publish/` (+ `hosting-options.md`) | Export, hosting routes, troubleshooting |
| `skills/byor-config-editor/` | Add, remove, rename domains, quadrants, rings |
| `skills/byor-radar-update/` | Half-yearly update: only what changed, about 25 minutes; saves a snapshot and rebuilds the site |
| `.../references/plain-language.md` (under builder) | Wording rules for every message: short sentences, plain words, no filler or buzzwords |
| `skills/byor-radar-share/` (+ `contribution-format.md`, `consent-and-redaction.md`) | Member side of a consortium round |
| `skills/byor-radar-convene/` (+ `round-lifecycle.md`) | Convener side of a consortium round |

## Scripts
| Path | Purpose |
|---|---|
| `scripts/freeze_edition.py` | Names the edition, marks what changed, saves `editions/<id>.json`, keeps the newest four |
| `scripts/compare_editions.py` | Compares two editions; writes `changes.json` and `changes.md` |
| `scripts/lint_plain.py` | Checks the example wording in skills for buzzwords, filler, jargon, long sentences, double questions |
| `scripts/state_to_radar.py` | State to BYOR CSV/JSON (`--compat`, `--full`, `--print-env`); CSV formula guard |
| `scripts/validate_radar.py` | Radar linter |
| `scripts/build_site.py` | State to single-page radar site (escaped, CSP, no external loads) |
| `scripts/radar_stats.py` | Progress and coverage |
| `scripts/check_config.py` | Config consistency (needs PyYAML) |
| `scripts/serve_local.sh` | BYOR in Docker, bound to localhost, read-only mount, optional pinned image |
| `scripts/registry.py` | Tool registry: resolve, match, check, add |
| `scripts/state_to_contribution.py` | State + kit + profile to share-safe contribution (with preview) |
| `scripts/validate_contribution.py` | Strict validator for contributions and round kits |
| `scripts/refresh_share_profile.py` | Pre-fills a new round's share profile from the latest radar and the previous profile; moves real use forward |
| `scripts/compare_rounds.py` | Compares two rounds' aggregates: trends and comparability warnings |
| `scripts/aggregate_round.py` | Convener intake and aggregation (minimum 3, anonymity rules) |
| `scripts/build_benchmark.py` | Benchmark site, private member reports, narrative validation |
| `scripts/set_owner.py` | Set or rename owner, repo, ref everywhere; regenerates URL block and bundle |
| `scripts/build_bundle.py` | Regenerates `BUNDLE.md` |
| `scripts/verify_deploy.py` | Post-deploy URL smoke test |
| `scripts/audit.sh` | Read-only security self-audit |

## Templates, docs, examples, tests
| Path | Purpose |
|---|---|
| `templates/radar-state.template.json`, `blip.template.json` | Radar state and blip shapes |
| `templates/blip-description.md`, `radar-summary.md` | Writing templates |
| `templates/consortium/round-kit.template.json`, `share-profile.template.json` | Round kit and member share profile |
| `docs/ROADMAP-TIME.md` | Change over time: editions (built) and rounds over time (proposal) |
| `docs/CONSORTIUM.md` | How consortium rounds, the benchmark site and member reports work |
| `docs/consortium-charter-template.md` | Charter template (not legal advice) |
| `examples/sample-radar-state.json`, `examples/output/` | Fictional radar, its CSV/JSON and site |
| `examples/consortium/` | Kit, share profile, 5 synthetic contributions, roster, narrative, aggregate, benchmark site, member reports; round 2 (`round-kit-2.json`, `inbox-2/`, `round-output-2/` with trends) |
| `evals/evals.json` | 33 behavioural scenarios for AI clients |
| `tests/test_scripts.py` | 45 tests: export, validation, injection, privacy rules, rename, editions, plain-language lint |
