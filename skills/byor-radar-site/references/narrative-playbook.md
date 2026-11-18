# Narrative playbook

## Taglines (canonical spirit: opinionated, plain, about the landscape)
- "An opinionated guide to <org>'s software landscape"
- "What we use, what we are trying, and what we would warn a colleague about"
- "Our experience with the tools that run <org>"

## Theme candidates and the question that unlocks each
| Pattern (spot it in data) | Unlock question |
|---|---|
| Overlap: 2+ Adopt/Trial in one domain | "If you could keep only one, which, and what would you lose?" |
| Open source momentum: several (FOSS) blips in Assess/Trial | "What would have to be true for you to trust it in production?" |
| Security/identity gaps: empty or Caution in access-control, endpoint | "What is the thing you would most worry about if it failed tomorrow?" |
| AI adoption: ai-tools blips | "Where is AI helping and where are you not letting it near data?" |
| Renewal cliff: many `next_review` or contract dates close together | "What is the decision you must make before the next renewal?" |
| Shadow IT: tools staff chose themselves | "Why did people go around the standard tool?" |
| Consolidation into suites (e.g. one productivity suite replacing several) | "What did the suite make easier, and what got worse?" |
| Cloud/vendor lock-in | "What would leaving cost, in months?" |
| Data and integration: tools not talking to each other | "Which manual copy-paste would you remove first?" |

## Theme template (90-180 words)
> **<Title: a phrase, not a sentence>**
> <Pattern in one sentence, linking [[Blip A]] and [[Blip B]].> <Nuance or tension, a second pair of blips.>
> <Caution: "We caution against ..." if a Caution blip is involved.> <Looking ahead: "In the coming months we may see ...".>

Rules: only facts from the user or verified public facts (tagged "public info"); no hype; no vendor adjectives; no blaming
people. Blips referenced as `[[Exact Name]]`; the generator turns them into links and warns on unknown names.

## Intro template
"This radar is a snapshot of the software <org> uses, is trialling, is exploring, and is wary of. It reflects the
experience of <who>. It is an opinion based on our own work, not a market survey, a vendor ranking or a list of approved
products."

## Actions
Verb first, one owner, one date or trigger: "Migrate the knowledge base off X before renewal (IT lead, before June)".

## FAQ customisation
The generator's FAQ covers: what the radar is, approved list or not, how rings are decided, position and shape meaning,
why a tool is missing, how blips change, how to suggest one, cadence. The user may override `meta.how_to_nominate`.
