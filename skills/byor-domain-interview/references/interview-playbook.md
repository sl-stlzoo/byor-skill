# Interview playbook

## Wording bank
- Inventory: "What tools do you use for <domain>? Spreadsheets and 'someone's personal account' count."
- Pipeline: "Are you testing or looking at anything new?"
- Exits: "Is there something here you'd tell a new colleague *not* to start using?"
- Ownership: "Who would be called if <tool> broke on Monday morning?"
- Renewal: "Do you know when <tool> comes up for renewal, roughly?"
- Integration: "Which other systems does <tool> talk to?"
- Adoption: "Do most, some, or few of the right people use it?"
- Exit cost: "If you had to leave <tool> within a year, how painful would that be? Easy, moderate, hard."
- Data: "Could you export all your data today?"

## Probing techniques
- **Vague answer:** if you hear "it's fine", ask "What stops you from calling it Adopt?" Never ask "Can you tell me more?"
- **Temporal anchors:** "since when", "how long in production" beat "is it mature".
- **Overlap:** "If you could keep only one of the two, which one?" This shows where tools overlap.
- **Numbers with ranges:** accept "about 40" or "dozens". Do not push for precision.

## Awkward answers
| Answer | Response |
|---|---|
| "No idea, IT handles it" | Offer to mark `confidence: low` and suggest asking IT; continue. |
| Long rambling list | Condense into a list, confirm, then ask which 3-6 matter. |
| "We use everything" | Ask for the top two by usage and any one they would drop. |
| Mentions a person's performance or complaint | Redirect to the tool's fit, do not record the person. |
| Mentions a security incident | Record factual summary only ("past incident, resolved") and flag for the Hold/risk discussion; avoid details. |
| Mentions a price under NDA | Do not record the price. |
| Asks "which should we buy?" | Offer decision criteria from `lens`; record candidates as Assess. |

## Depth guide
- quick: Steps A, B, D, one probe, hand-off
- standard: Steps A-E, seed menu if sparse, hand-off
- deep: all steps, plus ownership, renewal, integration, adoption and exit-cost for each candidate

## Domain notes (extra care)
- **access-control**: separate physical and digital credentials into distinct blips.
- **ticketing**: confirm admissions ticketing vs work tickets; move work tickets to itsm-helpdesk.
- **cash-counting**: record fully cashless as a skip reason, not a software blip. For mixed sites, cover those that accept cash.
- **Shared suites**: if one tool covers several areas (such as ticketing and admissions POS, or ERP and purchasing), use one blip and record the other areas in `also_in`.
- **wealth-screening**: ask about consent and privacy policy; never record donor names or amounts.
- **ai-tools**: ask about data-handling policy and shadow use; record self-hosted vs vendor-hosted.
- **public-cloud**: one blip per provider, plus "technique" blips such as "Infrastructure as code" if raised.
- **endpoint-security**: separate EDR from device management if the user treats them as different tools.
- **telephony** vs **call-center**: a phone system and a contact-centre platform may be one product; use one blip
  in the primary domain and `also_in` for the other.
