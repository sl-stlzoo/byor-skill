---
name: byor-radar-update
description: Guides a returning user through the next half-yearly edition of their own radar in about 25 minutes instead of two hours. Loads the previous edition, asks only about what may have changed (tools still in use, ring changes with a short reason, new tools, tools stopped, open actions), marks what changed automatically, saves a snapshot, and rebuilds the website with a "What changed" section and a history for each tool. Use this skill whenever the user says update, refresh, redo, next edition, half-year, quarterly, "what changed since last time", or has an earlier radar-state.json or editions folder, even if they say they want to start over.
---

# BYOR Radar Update (the next edition)

Every question follows `byor-radar-builder/references/plain-language.md`: short sentences, plain words, one question at a time, no filler.
Editions are half-yearly by default (2027-H1 is January to June, 2027-H2 is July to December). The newest four snapshots are kept (three before this one, plus this one).
Snapshots are plain JSON files in `editions/`. Nothing else is needed to compare.

## Start
Find the last edition: `radar-state.json` with `meta.edition`, or the newest file in `editions/`. No earlier edition? Use the normal workflow instead.
Set the new edition id from today's date (for example 2027-H1) in `meta.edition`. Do not ask.

> Your last radar is 2026-H2. Do you want a quick update or a fresh start?

Options: Quick update (about 25 minutes) / Fresh start. Fresh start: go to the normal workflow, but keep the old snapshots.

## Quick update: ask only these, in this order

1. **Context.** > Is your organisation and purpose the same as last time?  (Yes / Something changed.) If changed, update `meta` and ask the one or two things that changed.
2. **Rings.** > Do Adopt, Trial, Assess and Caution still mean what they meant last time?  (Yes / No, I want to change them.) If no, redo Phase 4 only.
3. **Review the tools, riskiest first.** Order: tools past `next_review`, then Caution, then Trial, then Assess, then Adopt, grouped by domain. Say how many there are and offer to bulk-confirm the ones with no change at the end.
   For each tool:
   > Do you still use Zendesk?
   Options: Yes, no change / Yes, but my view changed / No, we stopped / Not sure.
   - **Yes, but my view changed:** > Is it better or worse than before?  (Better / Worse.) Then propose one step: > That moves it from Trial to Adopt. Adopt means you would tell anyone to use it. Agree?  (Yes / No, a different stage.) Then: > Why? A few words are enough.  Save the words in `ring_reason`.
   - **No, we stopped:** > Why did you stop?  (Replaced it / Too costly / It did not work / Not needed / Something else.) Remove it from `blips`, and add `{name, tool_id, reason}` to `dropped[]`.
   - **Not sure:** keep it as is and set `confidence` to low.
   - **Time-in-ring nudge:** if a tool was Trial in the last two snapshots, ask > You have used it for a year now. Is it ready for Adopt?  If it was Assess twice in a row, ask > Are you still looking into this? Keep it, or drop it?
   Review rule: a move toward Adopt needs real use. If the tool has under 6 months of real use, say so and offer Trial instead.
4. **New tools, one domain at a time.** > Any new tools for CRM since 2026-H2?  Only new ones go to `byor-domain-interview` and `byor-blip-assessor`. Look up the tool in the tool list quietly (see `byor-domain-interview`); ask only if you cannot find it.
5. **Actions from last time.** For each: > Last time you planned: "Move the helpdesk off Zendesk". Is it done?  (Done / Started / Not yet / Dropped.) Save in `actions[].status`.
6. **New actions.** > What will you do before the next update?  Offer to draft one to three from the changes.
7. **Confirm what did not change.** Show the unchanged tools in one short list. > These did not change. Is that right?

## Save and build
1. Say: > I will save this edition and mark what changed. I keep your last four editions, which is two years. Older ones are deleted. Ready?
2. Run `python scripts/freeze_edition.py radar-state.json`. It sets New, Moved In, Moved Out or No Change on every tool, and saves `editions/<id>.json`. Add `--force` only if the user confirms they want to replace this edition.
3. Run `python scripts/compare_editions.py radar-state.json` and read the summary aloud in plain words (new, moved, dropped, actions).
4. Ask for the story: > What is the main story of this half-year?  Offer two or three options taken from the changes (for example "Fewer tools, clearer owners"). Write or update `themes` with `byor-radar-site`.
5. Run `python scripts/build_site.py radar-state.json` and `python scripts/state_to_radar.py radar-state.json`. The site now has a "What changed" section, a history line on every tool whose ring changed, and a list of earlier editions.
6. Run `byor-radar-validate` and `byor-radar-publish` as usual. Remind them about privacy once, as in the normal workflow.
7. Set `meta.next_review` to six months out and offer a reminder if the platform has one. Ask first.

## Without code execution
Do the comparison by hand from the two states: list new, moved and dropped tools in plain words, set `status` and `isNew` on each tool yourself, and print the new state as a code block for the user to save as `editions/<id>.json`. Tell them to keep the last four.

## Rules
- Never delete a snapshot except as the freeze script does (oldest beyond four), and only after the user said yes to the save message.
- Never invent a reason. If the user gives none, leave `ring_reason` empty.
- Do not re-ask what is already in the last edition.
- A move needs the user's yes. You may propose, never decide.
