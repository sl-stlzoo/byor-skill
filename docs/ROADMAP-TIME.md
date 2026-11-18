# Roadmap: change over time (design, not yet implemented)

Status: **Axis A (editions) is built. Axis B is partly built**: member continuity and round-over-round trends from published aggregates are in; panel analysis (same organisations over time, with an opt-in ledger) is still a proposal. Two time axes, in priority order:

**Decisions made:** (1) opt-in longitudinal retention for rounds is acceptable, but keep it simple: it need not be sealed or fully self-contained, and it adds as little upkeep as possible; (2) editions are **half-yearly** by default (2027-H1, 2027-H2) and the newest **four** snapshots are kept (three previous plus current, about two years); (3) every tool gets a registry id **during the interview**, quietly, with plain-language questions only when a match is unclear; (4) public trends show **both** all members and the returning cohort.

**A. one organisation over time (editions)**, the default case; **B. many organisations over time (rounds)**.

## Linchpin: stable tool identity
Both axes need to know that "Office 365" in Q1 and "Microsoft 365" in Q3 are the same tool. Plan: every blip in `radar-state.json` gets a registry `tool_id` (silent auto-match during the interview, a question only when ambiguous; `custom` ids for unlisted tools). The registry gains additive-only aliases, ids that are never reused, and a `merged_into` migration map when two ids are consolidated.

## A. One organisation over time: editions  (BUILT in v1)

What shipped: `scripts/freeze_edition.py` (names the edition, sets New / Moved In / Moved Out / No Change, saves `editions/<id>.json`, keeps four), `scripts/compare_editions.py` (diff, change log, numbers), `scripts/registry.py annotate` (quiet tool ids), the `byor-radar-update` skill (about 25 minutes, plain questions), a "What changed" section, per-tool history and an editions list on the site, `scripts/lint_plain.py` and `plain-language.md` (wording rules). Left out on purpose to keep upkeep low: hashes and signing of snapshots, merge tooling, dashboards. Snapshots are plain JSON files you can copy, read or delete by hand.

Original design notes follow.


**Concept.** A radar is an *edition* (for example 2027-Q1). The working file stays `radar-state.json`; each published edition is frozen as an immutable snapshot `editions/2027-q1.json` (with a hash and an `editions/index.json`). Change is always computed between snapshots, never typed by hand.

**Guided "update my radar" path (new Phase 0 branch).** The agent detects a previous snapshot and offers: *Update (about 20-30 minutes)* or *Start fresh*. Update walks only what changed:
1. Confirm context and rings are unchanged (or note drift in ring criteria).
2. Review-due first: blips past `next_review`, then every Caution and Trial item.
3. Per domain, one pass: "Still using X? Anything new, retired, or rated differently? Anything now with more real use?" Bulk-confirm unchanged tools.
4. Carry open actions forward and ask whether they are done.
5. Ask for the *reason* behind every ring move in a few words (feeds themes and the change log).

**Computed outputs.**
- Automatic `status`: New, Moved In (toward Adopt), Moved Out (toward Caution), No Change, and a **Dropped** list (in the last edition, absent now, with reason). `isNew` becomes "new since the last edition". The BYOR CSV status column is filled for you.
- **Change log** ("What changed this quarter") and a themes prompt seeded with the biggest moves.
- Site additions: a "Changes since last edition" section, per-tool ring timeline, an editions archive page, portfolio metrics (tools per domain, consolidation, Caution count, time in ring, review hygiene, action completion).
- A guard: ring changes without a stated reason or with contradicting evidence (for example Trial to Adopt but real use still under 6 months) are flagged.

**New pieces.** `scripts/compare_editions.py` (diff, statuses, metrics), `scripts/freeze_edition.py` (snapshot and hash), state schema v2 (`edition`, `tool_id`, `previous_edition`, `ring_reason`, `actions[].status`), `byor-radar-update` skill, site "Changes" section.

## B. Many organisations over time: rounds  (trends BUILT, panel analysis not yet)

What shipped: kit fields `previous_round_id` and `sequence`; `scripts/compare_rounds.py` (adoption in 5-point steps, consensus changes, appeared and gone tools, calibration shift, comparability warnings, no ring counts); `merged_into` and `registry.py merge` for tool ids; `scripts/refresh_share_profile.py` (carry over, move real use forward, flag what is new); a real-use-goes-backwards warning at export; a Trends section on the benchmark site. Original design notes follow.


**Two kinds of comparison, kept separate**
1. **Cross-sectional trend** (aggregate to aggregate): adoption share, consensus ring, flags, composition, for each tool that has at least 3 organisations in *both* rounds. Cheap, needs only retained `aggregate.json` files, but confounded when members join or leave. Always show the returning-cohort size next to the trend and label cohort changes.
2. **Panel movement** (same organisations in both rounds): transition matrix (Adopt to Trial, Trial to Caution, and so on), tools added or dropped, evidence maturing. This separates opinion change from sample change.

**Governance problem to settle first: retention versus privacy.** The charter deletes raw files after a round, but panel analysis needs the same organisation's earlier answers. Proposed resolution: an **opt-in longitudinal consent** per member. Opted-in members' contributions are retained by the convener as a minimised **panel ledger** (org id, tool id, effective ring, experience, scale, round; no free text) for a stated number of rounds. Members who do not opt in appear in cross-sectional trends only.

**Privacy rules that must extend over time**
- Minimum cohort 3 applies to every published transition cell and to the returning cohort.
- **Differencing across releases** is a real attack: two aggregates that differ by one entrant or leaver can reveal that organisation's rating. Publish panel movement only as suppressed transition counts (cells below 3 hidden), never as raw deltas on small cohorts, and warn the convener when cohorts differ by fewer than 3 members.
- Anonymous members keep continuity through a convener-held `org_id` in the roster; their trajectories are published only inside k-anonymous cells.
- Private "your trajectory" reports show a member their own changes against peer movement, built from their own files plus k-anonymous aggregates.

**Versioning and comparability**
- Kit adds `sequence`, `previous_round_id`, and a comparability declaration (same rubric version? same domain list? same registry lineage?). Anything different is labelled "not directly comparable".
- Registry migration map is applied before comparing; ids are never reused.
- Rubric changes bump `rubric_version`; calibration answers are trended so a change in how strict members are is visible.
- Contributions carry `as_of` and, optionally, a link to the member's previous contribution. A consistency check warns when an experience bucket fails to advance with time (for example "under 6 months" in two rounds a year apart).

**New pieces.** `scripts/compare_rounds.py` (aggregate trends plus, with a ledger, panel transitions), registry migration support, `round.sequence` and comparability fields, benchmark site "Trends" section and a rounds timeline, member "your trajectory" section, charter clause for longitudinal consent and ledger retention, tests for differencing across releases, evals for cohort-change confounding.

## Member continuity (bridges A and B)
When a member has editions, `byor-radar-share` pre-fills from the latest snapshot and the previous share profile (tool mapping, calibration, attribution) and shows only the delta since the last contribution.

## Suggested build order
1. **Editions foundation:** `tool_id` in state, snapshots, `compare_editions.py`, automatic status, change log, site Changes section and timeline, `byor-radar-update` skill.
2. **Member continuity:** refresh share profile from the latest snapshot; experience-consistency warnings.
3. **Round trends (cross-sectional):** `compare_rounds.py` on aggregates, registry migration, comparability flags, benchmark Trends section.
4. **Panel analysis:** longitudinal consent and ledger, transition cells with suppression, private trajectory reports.
5. **Later:** hosted archives, signed contributions, automated reminders for quarterly updates.

## Decisions needed
1. Is opt-in longitudinal retention (the panel ledger) acceptable, or should rounds stay strictly cross-sectional?
2. Edition naming and cadence defaults (quarterly, half-yearly), and how long snapshots are kept.
3. Resolve every blip to a registry `tool_id` during the individual interview (recommended), or only at share time?
4. In public trends, show all members, returning cohort only, or both side by side (recommended)?
