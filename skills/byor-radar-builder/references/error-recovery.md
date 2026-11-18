# Error recovery

| Situation | What to do |
|---|---|
| User returns after a break | Read state, say where they left off in one sentence, offer Continue / Review so far / Change something. |
| State file missing or corrupt | Say so plainly. If a snapshot exists in the chat, rebuild from it. Otherwise restart at Phase 0 but reuse anything the user still has in the conversation. |
| Cannot fetch a repo file | Try the raw URL, then `BUNDLE.md`, then ask the user to attach or paste. Never improvise the missing instructions silently; tell the user what was unavailable and what default you used. |
| Cannot run code | Use CHAT-SNAPSHOT mode; do validation manually using the checklist in `byor-radar-validate/SKILL.md`; print CSV for the user to save. |
| No web access | Set evidence mode to `user-only`. Skip seed verification; label seeds as unverified suggestions. |
| User says "I don't know" about a tool | Record the name with `confidence: low`, ring `assess` only if they actually plan to look at it, otherwise leave it as an "unrated" note in `domains[x].notes` and revisit in Phase 6. Do not guess. |
| User lists too many tools in one domain | Group: "Which 3-6 matter most for decisions?" Others go to `notes` or one summarising blip such as "Misc. marketing plugins". |
| Same tool in two domains | See `state-schema.md` (primary domain + `also_in`). |
| User disagrees with the ring rubric | Their definition wins. Edit the ring criteria in state (Phase 4 can be reopened) and re-check earlier blips only if they ask. |
| User wants to change quadrants mid-way | Allowed. Update `quadrants` and each domain's `quadrant`; blips follow their domain. Re-run the checkpoint for affected quadrants. |
| User wants to add a domain not in config | Run `byor-config-editor` quick-add: id, name, quadrant, scope, 2 probes; no seeds needed. |
| Everything lands in Adopt | Run the "evidence challenge" in `byor-blip-assessor/references/ring-rubric.md` for three random items; ask what has been stopped or avoided. |
| User asks which tool to buy | Give neutral decision criteria from the domain `lens`, and offer to add the candidates as `assess` blips. Do not recommend a vendor. |
| Sensitive content in descriptions | Remove or generalise; confirm with user. |
