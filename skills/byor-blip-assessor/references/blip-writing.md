# Writing blip descriptions

BYOR shows the description when a user clicks a blip. Write for a colleague who has 20 seconds.

## Structure (30-110 words)
1. **What and why here:** one sentence. "<Tool> is how we <job> for <who/where>."
2. **Why this ring:** "<Ring>: <concrete evidence or reason>."
3. **Watch-outs:** one sentence, the biggest risk or limit.
4. **Next step or guidance:** an instruction a reader can follow. "Use for new X; review in <month>."

## Style
- Plain, specific, present tense, active voice. No hype, no vendor slogans.
- Numbers only if the user gave them. Dates as "March 2027" or "Q1 2027".
- Public facts are tagged: "(public info)". Example: "The vendor announced end of support for v7 in 2027 (public info)."
- No people's names, credentials, internal URLs, prices under NDA, or security incident details.
- Allowed HTML (BYOR sanitises): `<b> <i> <a href> <ul><li> <br> <p> <code>`. Prefer plain text.
- Avoid double quotes and line breaks where possible; the export script quotes CSV correctly, but plain text reads better.

## Ring-specific phrasing
- Adopt: "Default choice for ..."
- Trial: "Piloting in ...; success measure: ..."
- Assess: "Exploring because ...; next step: ..."
- Caution: "We had a poor experience with ...; consider alternatives. Plan to ... by ..."

## Examples
- Adopt: "Microsoft 365 provides email, files, chat and meetings for all staff. Adopt: company-wide for four years with MFA enforced. Watch-out: sharing settings are too open. Default for collaboration; review external sharing quarterly."
- Assess: "CiviCRM is being explored as an open source alternative to our paid member database. Assess: only a demo instance exists with no live data. Next step: a data-migration proof of concept and a hosting cost estimate."
- Caution: "Zendesk is used for IT requests by two staff. Caution: licence cost is high for the usage and a bundled helpdesk is available elsewhere. Avoid new use and plan migration before renewal."

## Checks before saving
Word count in range; ring and reason agree; no sensitive facts; the next step is something a person can do.
