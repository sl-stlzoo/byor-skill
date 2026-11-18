---
name: byor-blip-assessor
description: Turns a candidate tool from a domain interview into a finished radar blip by choosing the ring (Adopt, Trial, Assess, Caution) with an explicit rubric, deciding isNew and status, naming an owner, and writing a short description that BYOR can display. Use this skill whenever the radar builder or the user needs to rate, place, re-rate, justify or describe a tool on the radar, or tailor what Adopt, Trial, Assess and Hold mean for their organisation.
---

# BYOR Blip Assessor

Input: candidate records from `byor-domain-interview` (or a single tool the user names).
Output: complete blip objects appended to `radar-state.json` (schema in `byor-radar-builder/references/state-schema.md`).

## Phase 4 mode: tailor the rings
When called from Phase 4, walk the user through the four rings **one per message**, using
`references/ring-rubric.md` and `config/rings.yaml`:
1. Show the ring's default meaning and 3-4 default criteria.
2. Ask (tappable): "Keep as is / Edit / Replace". On Edit, take their wording.
3. Ask one organisation-specific criterion: Adopt "what must be true before you'd call a tool a standard?",
   Trial "how long and how big is a pilot here?", Assess "who may start exploring?", Caution "who decides to move away, and what counts as a bad experience?".
4. Save to `state.rings[i].criteria`. After all four, read back the full set as a table and get a final yes.

## Rating mode (default): per candidate
Use `depth_profile.rubric_questions` (2 / 4 / 6) to decide how much to ask. Ask only what is not yet known.

1. **Real use** (always): "How long have you used it for real work?" Then: "How many people use it?"
2. **Fit** (always): "Does it do the job, or do people work around it?"
3. **Owner** (4+): "Who owns it on the business side?" Then: "Who runs it day to day?"
4. **Risk** (4+): "Has anyone checked its security?" Then: "Could you leave it if you had to?"
5. **Direction** (6): "Do you want to use it more, the same, or less?"
6. **Cost** (6): "Is the cost fair for what you get?" Then: "How hard would it be to leave?"

Then **propose a ring** with a one-sentence reason from the rubric, and ask the user to confirm or change it
(tappable: Agree / Higher / Lower / Different; say it plainly: "I would put this in Trial, because you have used it for 4 months. Agree?"). Their decision wins; record the reason in `decision_notes`.

### Ring decision rules (summary; full text in `references/ring-rubric.md`)
- `using` and criteria met -> Adopt. `using` with gaps -> Trial, or Adopt with watch-outs (ask which).
- `pilot` with real work run through it -> Trial; demo or sandbox only -> Assess. `evaluating` or `idea` -> Assess. `retiring`, `rejected`, or end-of-life -> Caution.
- Ask optional `radial` (0-1, closer to the inner ring = more confident) at standard and deep depth.
- Strong direction "less", a negative experience, or unacceptable risk overrides stage -> Caution.
- Unknown evidence -> do not Adopt; choose Assess or Trial and mark `confidence: low`.

### isNew and status
- `isNew` follows the Phase 1 setting. In later editions compare with the previous CSV: unseen names are new.
- `status`: leave blank on the first edition. Later: `New`, `Moved In` (toward Adopt), `Moved Out` (toward Caution),
  `No Change`. The export includes the `status` column only if at least one blip has a value.

### Writing the description
Follow `references/blip-writing.md`: 30-110 words, four sentences (what, why this ring, watch-outs, next step), plain
language, only facts the user gave or verified public facts tagged `(public info)`. Show the user the description and
accept edits. Never invent numbers, dates or incidents.

### Evidence mode
- `user-only`: no web. Everything comes from the user.
- `web-assisted`: you may verify the product's current name, ownership, licence (open source vs proprietary),
  end-of-life or end-of-support announcements and security advisories. Put source URLs in `evidence`, set
  `confidence`, and tag public facts in the description. Never put sensitive user facts into search queries. If a
  public fact contradicts the user, ask politely which is right.

### Save
Append or update the blip with: `name, ring, quadrant (from domain), domain, isNew, status, description, owner,
confidence, evidence[], last_reviewed (today), next_review (today + cadence if known), decision_notes`.
Set `domains[domain].status = "done"` when all candidates are saved.

## Domain wrap-up (after the last candidate)
Show a compact table (tool | ring | reason). Ask "Happy with these?" and apply edits. Run a quick balance check:
every candidate placed? duplicates with other domains? everything in one ring? Mention what you see in one line.

## References
- `references/ring-rubric.md`: decision grid, evidence challenge, open source vs commercial questions, sanity ranges
- `references/blip-writing.md`: description structure, style, examples, pre-save checks
