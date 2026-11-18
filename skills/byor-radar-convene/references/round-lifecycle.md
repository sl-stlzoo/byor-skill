# Round lifecycle, checklists and policies

## Timeline (typical)
| Week | Step | Owner |
|---|---|---|
| 0 | Counsel reviews charter; convener designs the kit and roster | Convener |
| 1 | Kit, charter, repo link and zip sent to members | Convener |
| 1-4 | Members build radars and contributions (`byor-radar-share`) | Members |
| 4 | Deadline; intake; follow up on rejected files | Convener |
| 5 | Aggregate, narrative, site, private reports | Convener |
| 6 | Distribute; members discuss | Convener / members |
| 8 | Delete raw files per charter; archive aggregate | Convener |

## Convener workspace layout
```
round/
  round-kit.json   roster.json   narrative.json
  inbox/                                  # raw contributions: CONFIDENTIAL, scripts only
  round-output/
    aggregate.json                        # members-safe
    benchmark/index.html                  # for all members
    member-reports/<org>.html             # private, one per member
    _convener/intake-report.md|json  anon-names.json   # CONVENER ONLY
```

## Intake checklist
- Files arrive through the agreed secure channel; verify sender identity out of band (the file hash is tamper evidence, not a signature).
- Run the aggregator; read only the intake report.
- Typical rejection reasons: wrong round or kit hash, stale registry version, unregistered tool, consent not true, markup in a name, file edited after export (hash mismatch), not on roster, over 1 MB. Ask the member to regenerate with `byor-radar-share`; never edit their file.
- Duplicates: the newest file per organisation wins; older ones are marked superseded.

## Privacy and anonymity policy implemented by the scripts
- No output at all below 3 accepted organisations (exit code 2).
- Tools need 3+ organisations; domains need 3+ organisations assessing them; profile and calibration cells below 3 show `<k`.
- Anonymous ratings join totals only when 3+ anonymous organisations used the tool; otherwise totals are named-only.
- Slices by sector and region need 3+ organisations in the slice and a k-anonymous basis.
- Named organisations appear with their individual ratings and optional 140-character rationale.
- Ratings are reinterpreted by evidence: Adopt with under 6 months real use counts as Trial; Trial with no real use counts as Assess. The count of reinterpreted ratings is published.

## Retention and deletion (recommended charter terms)
1. Keep raw contributions only until the round is closed (suggest 30 days after distribution).
2. Delete `inbox/` and `round-output/_convener/`; empty trash/recycle bin; remove copies from backups per your policy.
3. Keep: `round-kit.json`, `aggregate.json`, `narrative.json`, benchmark site.
4. Record the deletion date and who performed it.

## Second and later rounds
1. New kit with `previous_round_id`, `sequence`, same or newer registry version (record merges first).
2. Same roster, plus new members. Returning members use the refresh path in `byor-radar-share`.
3. Aggregate, then `compare_rounds.py old new`, then build the site with `--trends`.
4. Warnings to read aloud: rating rules changed; tool list changed without a migration map; kit does not name the old round; different organisations took part (more than 25% size change, or fewer than 60% of earlier named organisations returned).
5. Keep: kit, `aggregate.json`, `trends.json`, `narrative.json`, site. Delete raw files and `_convener/` on the charter date.
Trends use rounded adoption (5-point steps) and never show ring counts, to reduce what two releases can reveal together. They do not remove the risk entirely: with few organisations, a change can point to one organisation. Keep the benchmark informal.

## Failure modes
| Situation | Action |
|---|---|
| Fewer than 3 valid contributions | Extend deadline or recruit. Do not lower the cohort. |
| A member wants out after sending | Honour the charter's deletion process before aggregation if possible; after publication, aggregates cannot be unpublished |
| A member's anonymity is at risk (very distinctive stack) | Suppress that member's unusual tools by asking them to regenerate with them excluded, or raise the cohort |
| Narrative rejected | Remove names, URLs, markup, unknown tool links, or trim length |
| Member disputes their private report | The report is computed only from their file and aggregates; re-run with a corrected contribution |
| Pressure to reveal a subgroup or anonymous contributor | Decline; the charter and scripts prohibit it |
