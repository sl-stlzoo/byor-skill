---
name: byor-domain-interview
description: Runs a short, structured interview about ONE software domain (for example ERP, CRM, HRIS, endpoint security, public cloud, AI tools) to discover every tool in use, being piloted, being evaluated or being retired, and returns a clean candidate list for rating. Use this skill whenever the radar builder reaches a domain in a quadrant, or whenever the user wants to add, review or re-interview a single area such as "let's do CRM", "add another tool to accounting", or "what else do we use for security".
---

# BYOR Domain Interview

Interview the user about one domain at a time. Output: a **candidate list** with raw facts, handed to
`byor-blip-assessor`. This skill does not assign rings; it only discovers and clarifies.

## Inputs
- The domain record from `config/domains.yaml` (`name`, `scope`, `clarify`, `probes`, `seeds`, `lens`)
- `meta.depth` and its `depth_profile` from `config/settings.yaml`
- Existing blips for this domain from `radar-state.json` (if revisiting, start from them)

## Conversation contract (follow in order; stop early if the user is brief)

**Step A: Frame (1 message).** Read `scope` in one sentence, then ask the `clarify` question if the domain has one.
Offer: Let's go / Skip this area / Not applicable. If skipped, set `status: skipped` with a reason and return.

**Step B: Inventory (open question).**
"What do you use for <domain>? Include spreadsheets, free tiers and anything staff set up on their own."
Mirror back as a list, ask "Anything missing?" once. A "nothing yet" answer is valid and creates no blips.

**Step C: Pipeline.** "Anything you're piloting or looking at for <domain>?" Capture name + stage (idea, demo, pilot).

**Step D: Exits.** "Anything you're moving away from, regret, or want to stop others from adopting?"
Capture name + reason. These are Caution candidates (capture the negative experience as a fact).

**Step E: Domain probes.** Ask the domain's `probes` one at a time, up to `questions_per_domain` minus the questions
already asked in B-D. Use answers to enrich candidate facts (users, sites, contract date, integrations, owner).
Skip a probe if the user has already answered it.

**Step F: Seed menu (optional).** If `seed_menu` is true and the user's lists were short (fewer than 2 tools), show up to
8 seeds as a multi-select: "Do you use, test, or avoid any of these?" Prefer seeds that
fit the user's context (size, type). Say seeds are examples in alphabetical order, not recommendations. If
`evidence_mode` is `web-assisted`, quickly verify the seed names are current (renamed, acquired, discontinued) and drop
or relabel stale ones.

**Step G: Match to the tool list (quiet).** For each candidate, find the tool in our list so the same tool is never counted under two names. With code: `python scripts/registry.py annotate radar-state.json --write` after the domain is saved. It fills `tool_id` for exact matches and prints the rest. Do not mention this to the user.
For each tool it could not match, ask once, in plain words: "I could not find 'Zendeskk' in my list. Did you mean Zendesk?" (Yes / No). If no, keep the user's name and set `tool_id` to `x-` plus the name in lower case with hyphens. Never guess.

**Step H: Hand-off.** Build the candidate list (below), read it back in a compact list, and ask for a final
"Anything to correct?" Then pass control to `byor-blip-assessor`.

## Candidate record (hand-off format)

```json
{ "name": "Odoo POS", "domain": "retail", "stage": "using|pilot|evaluating|retiring|rejected|idea",
  "facts": ["2 sites", "pilot since September", "owner: shop manager"], "user_wants": "keep|expand|replace|unknown" }
```
Cap at `max_blips_per_domain`. If the user names more, ask which matter most for decisions; park the rest in
`domains[id].notes`.

## Rules
- Ask one question per message. Keep it short. Offer "Not sure" and "Skip".
- Never ask what is already in state or what the user just said.
- Use the exact name the user's staff would recognise (product name, not parent company).
- Distinguish products (Microsoft Teams) from capabilities (video calling); the radar lists products, techniques or
  patterns. Allow a "technique" blip (e.g. "Single sign-on everywhere") when the user raises a practice, and place it in
  the best-fit domain.
- If a tool clearly belongs to another domain, record it there and tell the user in one line.
- Treat open-source and commercial tools equally; note hosting model (self-hosted vs SaaS) in facts when relevant.
- Do not ask for costs unless `depth` is `deep` or the user offers them; never store NDA pricing.
- Respect the `lens` list: when a probe yields a worrying answer (no owner, no backup, unknown renewal date) note it as a
  fact for the assessor. Do not lecture.

See `references/interview-playbook.md` for question wording, probing techniques, and how to handle awkward answers.
