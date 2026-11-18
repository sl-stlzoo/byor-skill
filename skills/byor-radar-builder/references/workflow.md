# Workflow scripts (phases 0, 1, 3, 6, 10)

Wording below is a model, not a script to recite. Keep it short, adapt to the user's language and tone.
Phases 2, 4, 5, 7, 8, 9 are driven by their own skills/references; see SKILL.md.

## Phase 0: Welcome  <a id="phase-0"></a>
Goal: set expectations, pick depth and evidence mode.

Message 1 (no questions yet beyond the first):
> Let's build a radar of the software your organisation uses. I will ask about one area at a time, like ERP or CRM.
> For each tool, you pick a stage: Adopt, Trial, Assess or Caution. At the end you get a website and a data file.
> It takes about 5 minutes per area. You can stop and pick it up later.

Then the first question (tappable). Explain the stages only when you first ask for one, using the glosses in `plain-language.md`.

Question A: "How detailed should we be?"
- Quick: about 2 minutes per area
- Normal: about 5 minutes per area [recommended]
- Thorough: about 10 minutes per area

Question B (tappable, only if `evidence_mode: ask`): "May I look things up online to check tool names?"
- Yes, look things up
- No, use only what I say

Record `meta.depth`, `meta.evidence_mode`. Load `depth_profiles[depth]` from settings: it caps questions per domain,
blips per domain and rubric questions.

## Phase 1: Context  <a id="phase-1"></a>
Ask, one at a time (skip any already known):
1. Organisation name and type (company, nonprofit, school, public body, venue ...). Open question.
2. "Who is the radar for?" (leadership, IT team, all staff, board, partners). Tappable + other.
3. "What decision should it help with?" (renewals/budget, consolidation, security review, modernisation, onboarding
   new staff, other). Tappable + other. This sets the tone of descriptions.
4. Owner: "Who will keep the radar up to date?" (role is fine).
5. Do not ask about "new" or the name of the fourth ring. Defaults: in a first edition, a tool is new if you started it in the
   last 12 months; in later editions, new means new since the last edition. The fourth ring is called Caution.
6. Privacy reminder, once: "This radar shows which tools you use and where they fall short. Keep it private unless you choose to share it."
7. Say once: "This is the 2027-H1 edition." (Use the current half-year, for example 2027-H1 for January to June.) Save it as `meta.edition`. No question.

Write `meta.*`. Compute `meta.created` from today's date.

## Phase 3: Quadrant design  <a id="phase-3"></a>
Goal: exactly four quadrants and every active domain mapped.

Step 1 (keep this phase quick: the canonical radar treats quadrants as topic areas, not a big decision), scheme (tappable):
- Business domains (recommended for this domain list): the four names from `quadrants.yaml`, with default mapping
- Thoughtworks classic (Techniques / Platforms / Tools / Languages & Frameworks): best for engineering radars
- My own four names

Step 2, show the mapping as four short lists (one quadrant per message on small screens) and ask:
"Does this grouping look right?" If not: "Which area would you move?" Apply moves one at a time (a domain lives in exactly one quadrant).

Step 3, balance check: warn if one quadrant holds more than half of the active domains or any holds none. Suggest, do
not force.

Step 4, hosting implication (say once, briefly): custom quadrant names need a self-hosted BYOR (one Docker command) or
the "compat" export for the hosted site. Details come in Phase 8. Record `meta.hosting_hint`.

Write `quadrants[]` and `domains[id].quadrant`. Set `progress.phase = 4`.

## Phase 6: Calibration  <a id="phase-6"></a>
Goal: consistency across the whole radar. Three passes.

**Pass A, ring by ring (Adopt, Trial, Assess, Caution).** For each ring show all blips in it grouped by quadrant (compact:
`Tool - domain - 6-word reason`). Ask: "Does everything here belong in <Ring>?" Then: "Is anything missing?" Challenge gently:
- Adopt: "Would you tell anyone to use this?" Then: "Does it have an owner?" Then: "Do you know the renewal date?" Items failing the user's own criteria move down.
- Trial: "Has real work run through it?" If only a demo or sandbox, it is Assess.
- Assess: "What is the next step for this tool?" If nobody will do it, consider dropping it from the radar.
- Caution: "What went wrong?" Capture it as a fact. Is this "avoid for new use" or "move away"? Add the exit plan. Prompt for anything colleagues should avoid that did not come up (shadow IT, end-of-life products, misuse).

**Pass B, overlap and gaps.** Optional at deep depth: ask for radial position ("close to the next ring in, or only just in?") and save `radial` 0-1.

**Pass B (continued).** Look for: two Adopt tools doing the same job (consolidation candidate), domains with no
Adopt item (gap), domains skipped (confirm still skipped), tools appearing in several domains (merge per state rules).

Narrative (themes, intro, actions) now lives in Phase 7 (`byor-radar-site`).

Exit: user says the balance is acceptable. Set `progress.phase = 7`.

## Phase 10: Maintain  <a id="phase-10"></a>
1. Ask (tappable): "How often will you update this radar?" Twice a year (recommended) / Every three months / Once a year. Save `meta.cadence`. Default is twice a year: 2027-H1 and 2027-H2.
2. Say: "I will save this edition now. I keep the last four editions, which is two years. Older ones are deleted." Ask: "Ready?" On yes, run `python scripts/freeze_edition.py radar-state.json`. It saves `editions/<id>.json` and, from the second edition on, marks what changed.
3. Set each tool's `next_review` to the next edition date. Set `meta.next_review` (for example "2027-H2"). Offer a reminder if the platform has a tool for it. Ask first.
4. Tell the user how to update next time: "Next time, start a chat with the same link and say: update my radar. Bring your radar-state.json and your editions folder."
5. Without code execution: print the full state in a code block and tell the user to save it as `editions/<id>.json` and keep the last four.
Finish with the wrap-up described in SKILL.md.
