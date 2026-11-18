# Contribution format (schema `byor-consortium-contribution/1`)

Vocabularies: `config/consortium-vocab.json`. Registry: `config/tools.json`. Validator: `scripts/validate_contribution.py` (strict: unknown keys, free text, markup, URLs, `@`, wrong types and bad hashes are errors).

```jsonc
{
  "schema": "byor-consortium-contribution/1",
  "round": { "id", "registry_version", "rubric_version", "kit_sha256" },          // bound to the convener's kit
  "contributor": { "org_name", "attribution": "named|anonymous",
                   "profile": { "sector", "size_band", "region" } },
  "calibration": { "adopt_min_experience", "adopt_requires_owner", "adopt_requires_security_review",
                   "trial_requires_real_use", "caution_meaning" },
  "domains_covered": ["crm", ...],      // domains the member actually assessed (denominator for "not used")
  "domains_skipped": ["hris", ...],     // kit domains not assessed or excluded (NOT the same as "uses nothing")
  "blips": [ { "tool_id": "microsoft-365",             // registry id, or x-<slug> custom when allowed
               "domain": "business-productivity",
               "ring": "adopt|trial|assess|caution",
               "experience": "none|lt-6m|6-12m|1-3y|gt-3y",
               "scale": "pilot|team-or-site|organisation-wide",
               "caution_tags": ["cost","fit"],          // only on caution, max 4
               "rationale": "<=140 chars, named only" } ],
  "consent": { 4 booleans, all true },
  "generated": "YYYY-MM-DD",
  "integrity": { "sha256": "<hash of the canonical body>" }
}
```

## Design decisions
- **Tags and buckets instead of prose** keeps the file safe to process, comparable across organisations, and hard to abuse for prompt injection or defamation.
- **Evidence travels with the ring** (`experience`, `scale`, calibration answers) so the aggregator can interpret "Adopt" fairly and apply the canonical rule that Trial needs real use.
- **Covered vs skipped domains** distinguish "does not use any" from "did not assess".
- **Hash = tamper evidence, not authenticity.** It detects accidental edits. Signed contributions are a later step.
- **Anonymous** hides the name from members. The file always carries the name so the convener can run the roster and reject duplicates.
- Quadrants, descriptions, owners, dates, decision notes, themes and actions are never included.
