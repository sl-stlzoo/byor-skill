# Consortium benchmarks: how it works

An informal, offline way for many organisations to compare their radars. **Nothing is uploaded automatically.** People exchange small files; scripts do all the processing.

```
 MEMBER (each organisation)                          CONVENER
 ──────────────────────────                          ────────
 radar-state.json                                    round-kit.json  +  roster.json
        │  byor-radar-share (Phase 11)                      │  sent to members with the charter
        ▼                                                    ▼
 share-profile.json ──► contribution.json ──(secure channel)──► inbox/        (raw files: scripts only)
   (choices, consent)     (tool, domain, ring,                      │ aggregate_round.py
                           experience, scale, tags)                 ▼
                                                    round-output/aggregate.json   (anonymised, k-suppressed)
                                                                    │ LLM drafts narrative.json from this file only
                                                                    ▼ build_benchmark.py
              benchmark site (index.html)  ◄────────────────  for ALL members
              private report (<org>.html)  ◄────────────────  one per member, sent only to its owner
```

## The roles at a glance
| Role | Skill | Does |
|---|---|---|
| Member | `byor-radar-share` | Chooses named (default) or anonymous, maps tools to the registry, answers 5 calibration questions, adds experience/scale buckets and caution tags, previews exactly what leaves, consents, exports a validated `contribution.json` |
| Convener | `byor-radar-convene` | Designs the round kit and roster, runs intake and aggregation, drafts a narrative from the aggregate, builds the benchmark site and private reports, distributes, deletes raw files on schedule |

## What a contribution contains (and never contains)
Per tool: registry `tool_id`, domain, ring (Adopt, Trial, Assess, Caution), real-use bucket (none, under 6 months, 6-12 months, 1-3 years, over 3 years), scale (pilot, team or site, organisation-wide), up to four caution tags, and, for named members only, a 140-character rationale. Per organisation: name, sector, size band, region, five calibration answers. **Never:** descriptions, owners, dates, notes, themes, quadrants, prices, incidents, people. Format: `skills/byor-radar-share/references/contribution-format.md`.

## The benchmark site (for every member)
One static `index.html` (about 30 KB at five organisations, no external requests, light/dark, printable).

| Section | What you see |
|---|---|
| Header and stats | Round title, convener, date; number of organisations, tools benchmarked, tools hidden for being below the minimum, ratings reinterpreted |
| **What the round says** | The convener's 3-4 themes, each a short essay with links that jump to the tools discussed |
| **Highlights** | Four lists: peer consensus **Adopt**, **Contested** (peers disagree), **Caution watch** (a third or more rate it Caution), **Emerging** (mostly under six months of use) |
| **By domain** | A table per domain: tool and licence model, *used by* (n of organisations that assessed the domain), *peer rating* chip (consensus ring plus flags), *spread* bar of ring counts, common *cautions* (shown only when 3+ organisations gave the tag), and *who*: expandable list of named organisations with their own ring, experience, scale and rationale. Filter by ring or search by tool name |
| **Who took part** | Named organisations, count of anonymous ones, and composition by sector, size and region (cells under 3 show `<k`) |
| **By sector and region** | Consensus per slice, only where the slice has 3+ organisations |
| **How to read this** | The privacy and normalisation rules, rings explained, informal-benchmark disclaimer, `aggregate.json` download |

## The private "you vs the round" report (one per member)
A separate page generated from that member's own file plus the aggregate, labelled **Private to <org>**.

| Section | What it tells the member |
|---|---|
| Summary | Tools shared, how many align with peer consensus, how many differ, how many were not benchmarked (fewer than 3 organisations) |
| Your tools vs the peer consensus | Per tool: your ring (and a note if it was reinterpreted by evidence), peer consensus and number of organisations, and a verdict: aligned, more confident than peers, more cautious than peers, peers split |
| Widely used by peers, not in your radar | Tools used by at least half the organisations that assessed the same domain, which you did not list |
| You use these; peers are cautious | Your tools that peers rate Caution or flag as caution-watch |
| How strict are your rings? | Your five calibration answers beside the distribution across all organisations |

Because it is built from the aggregate, a member learns nothing about other organisations beyond what the benchmark site already shows. The convener sends each report only to its owner.

## How the numbers are produced (rules implemented in `scripts/aggregate_round.py`)
1. **Minimum cohort 3.** Fewer accepted organisations: no output at all. The kit cannot set a lower floor.
2. **Tool and domain thresholds.** A tool needs 3+ organisations; a domain needs 3+ assessing it; smaller items are hidden and counted.
3. **Evidence-aware ratings.** Adopt with under 6 months of real use counts as Trial; Trial with no real use counts as Assess. The number reinterpreted is published. This applies the canonical idea that Trial needs real experience and keeps differently calibrated organisations comparable.
4. **Anonymous contributors.** Never named. Their ratings enter a tool's totals only when 3+ anonymous organisations used it; otherwise totals use named organisations only, so an anonymous rating cannot be derived by subtraction (covered by a test).
5. **Consensus.** The most common effective ring; a tie shows as *split*; *agreement* is the share in that ring.
6. **Normal intake hygiene.** Strict validation, roster check, newest file per organisation, tamper hash, 1 MB cap.

## Running a round (convener, about an afternoon)
```
python scripts/validate_contribution.py --kit-only round-kit.json
python scripts/aggregate_round.py --kit round-kit.json --inbox inbox --roster roster.json --out round-output
#   read round-output/_convener/intake-report.md (never the raw files), then aggregate.json
python scripts/build_benchmark.py site round-output/aggregate.json --narrative narrative.json
python scripts/build_benchmark.py members round-output/aggregate.json --inbox inbox --kit round-kit.json
```
Then send `benchmark/index.html` to all members, each `member-reports/<org>.html` to its owner only, and delete `inbox/` and `_convener/` on the charter's date.

## Try it with the worked example
`examples/consortium/` holds a kit, five fictional organisations (two anonymous), their contribution files, the generated `aggregate.json`, the benchmark site and one private report per organisation.

## Over time
**Members.** In a later round, `byor-radar-share` starts from last time: `refresh_share_profile.py` carries over the organisation, attribution, calibration, tool mapping, scale and tags, and moves "real use" forward by the time that passed (for example "under 6 months", seven months later, becomes "6 to 12 months"). The member answers only about new tools, ring changes, Caution tags and anything unclear. Consent is asked again every round. A real-use answer that goes backwards is flagged.

**Convener.** The new kit names the previous round (`previous_round_id`, `sequence`). After aggregation, `compare_rounds.py old/aggregate.json new/aggregate.json` writes `trends.json` and `trends.md`, and the benchmark site gets a **Trends** section:

| Shown | How |
|---|---|
| Rising and falling adoption | Change of 10 points or more, in 5-point steps, for tools shown in both rounds |
| Peer rating moved | Consensus ring before and after (for example Assess to Trial) |
| New in the benchmark, no longer shown | Tools that crossed the 3-organisation threshold in either direction |
| Comparability warnings | Rating rules changed; tool list changed without a migration map; kit does not name the previous round; a different group took part |

It uses only the two published aggregates. It never shows ring counts or any change for a single organisation. Merged tools are matched through `merged_into` in `config/tools.json` (`python scripts/registry.py merge OLD NEW`).

**Not built yet.** Panel analysis (how the same organisations moved) would need an opt-in, minimised record kept by the convener between rounds; see `docs/ROADMAP-TIME.md`. Individual radars already keep half-yearly editions (`byor-radar-update`).

## Limits
The convener always sees raw files, so anonymity is from other members only. The file hash detects accidental edits but is not a signature; verify senders out of band. A benchmark of opinions from a few organisations is directional, not statistical. Not legal advice: use `docs/consortium-charter-template.md` with counsel. Security detail: `SECURITY.md` §15a (member) and §15b (convener).
