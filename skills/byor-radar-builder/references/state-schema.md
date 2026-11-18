# radar-state.json

Single source of truth. Template: `templates/radar-state.template.json`. Example: `examples/sample-radar-state.json`.

```jsonc
{
  "schema_version": 1,
  "meta": { "organization", "radar_title", "audience", "purpose", "created", "updated",
            "depth": "quick|standard|deep", "evidence_mode": "user-only|web-assisted",
            "hold_label": "Caution|Hold", "quadrant_scheme", "repo_base_url", "owner",
            "edition": "2027-H1", "previous_edition", "published", "tagline", "intro", "contributors": [{"name","role"}], "how_to_nominate",
            "cadence", "next_review", "site_title" },
  "progress": { "phase": 0-10, "current_quadrant": id|null, "current_domain": id|null,
                "last_checkpoint": ISO date|null, "notes": [] },
  "quadrants": [ { "id", "name" } ],                    // exactly 4
  "rings":     [ { "id": "adopt|trial|assess|hold", "name", "criteria": [..tailored..] } ],
  "domains": { "<domain-id>": { "name", "quadrant": <quadrant id>, "status": "pending|in_progress|done|skipped",
                                "notes": "", "skipped_reason": "" } },
  "blips": [ { "name", "ring": <ring id>, "quadrant": <quadrant id>, "domain": <domain id>,
               "isNew": bool, "status": ""|"New"|"Moved In"|"Moved Out"|"No Change",
               "description", "owner", "confidence": "low|medium|high",
               "evidence": ["user-stated","public info: <url>"], "last_reviewed": "YYYY-MM-DD",
               "next_review": "YYYY-MM-DD", "decision_notes": "",
               "tool_id": "registry id, or x-<slug> for a tool not in the list", "previous_ring": "set by freeze_edition.py", "ring_reason": "why it moved (a few words)",
               "radial": 0-1 /*optional: 0 = inner edge of ring, 1 = outer edge*/, "champion": "who writes it up" } ],
  "shares":  [ { "round_id", "date", "attribution", "sha256", "blip_count" } ],      // receipts only, no content (Phase 11)
  "themes":  [ { "title", "body": ["paragraph with [[Exact Blip Name]] links"] } ],   // 3-4, Phase 7
  "actions": [ { "action", "tool", "owner", "by", "status": "open|started|done|dropped" } ],
  "dropped": [ { "name", "tool_id", "reason" } ]                 // tools stopped since the last edition (update flow)
}
```

## Update rules
- Update `meta.updated` and `progress` on every write.
- Write after each answer that changes data; do not batch more than one domain.
- Blip names unique across the whole radar. If a tool serves two domains (e.g. HubSpot in CRM and Marketing), keep ONE
  blip in the domain where it is primary, mention the other use in the description, record
  `"also_in": ["marketing-communication"]`.
- A tool the user wants rated differently per use (e.g. "Teams chat: Adopt, Teams Phone: Trial") becomes two blips
  with distinguishing names ("Microsoft Teams (chat)", "Microsoft Teams Phone").
- Never delete a blip silently. Removing = set `ring: "hold"` or ask for confirmation then delete and add a note in
  `progress.notes`.
- `isNew` = true only if the tool has not appeared on a previous edition of this radar. First edition: set TRUE for
  tools adopted/started within the last ~12 months, otherwise FALSE (ask once in Phase 1 which meaning they prefer).
- Dates: ISO 8601. Use the date provided by the platform or ask the user.
- CHAT-SNAPSHOT mode: print `{"meta":..,"progress":..,"quadrants":..,"rings":..,"domains":..,"blips":..}` minified.
