# Security, Trust and Responsible Use

**Audience:** CIO, CTO, VP/Director of IT, security and risk leaders evaluating whether to let people use this skill set.
**Status:** v1.0, reviewed 14 November 2026 by the authors (self-assessed; see [§13](#13-assurance-statement-and-limits)).
**Companion files:** [`skills/byor-radar-builder/references/security-guardrails.md`](skills/byor-radar-builder/references/security-guardrails.md)
(rules the AI agent is told to follow), [`scripts/audit.sh`](scripts/audit.sh) (self-service audit), [`RUNBOOK.md`](RUNBOOK.md).

---

## 1. Executive summary

**What it is.** A set of text instructions and a handful of small local scripts. A person pastes one prompt into an AI assistant;
the assistant reads these instructions and interviews them about their organisation's software, then produces a data file for
[Thoughtworks Build Your Own Radar](https://www.thoughtworks.com/radar/byor) and a single-page static website.

**What it is not.** It is not a service, agent platform, browser extension or application you install. There is no server, account,
login, database, API key, analytics or telemetry in this repository. Nothing here phones home.

**The honest security position.**

| Question | Short answer |
|---|---|
| Does the repo contain executable code that touches the network? | No, with one maintainer-only exception (`verify_deploy.py`, HTTP GET to GitHub). Checked by `scripts/audit.sh`. |
| Does it need credentials, tokens or admin rights? | No. It tells the agent never to ask for them. |
| Can it change anything in your systems? | Not by design. It instructs the agent to stay read/write on local radar files only. Whether a client *enforces* that depends on the client's permissions, which you control (§9). |
| What is the main risk? | **Data you give an AI assistant, and the finished radar itself.** A radar is a map of your technology estate and its weak spots. Treat it as confidential. |
| Second risk? | **Supply chain and prompt injection.** The instructions are fetched live from GitHub, so whoever controls the repo influences what the agent does. Mitigation: pin a reviewed version (§9). |
| Is it independently audited? | **No.** It is open source, small enough to review in an afternoon, has an automated self-audit and security regression tests, and welcomes independent review. |
| Residual risk (artefact itself) | **Low**, when a pinned, reviewed copy is used with least-privilege client settings. |
| Residual risk (data handling) | **Low to high depending on what is entered and where the output is published.** That is a process risk, not a code risk. |

---

## 2. What is in the repository

| Component | What it is | What it can do | What it cannot do |
|---|---|---|---|
| `AGENTS.md`, `skills/**/*.md` | Natural-language instructions the AI follows | Shape the interview and outputs; tell the agent which files to read/write and which scripts to run | Execute anything itself. Their power comes entirely from the agent that reads them, which is why integrity and guardrails matter (§5) |
| `config/*.yaml` | Domain list, quadrant and ring definitions, limits | Change questions and example tools (a place where a malicious edit could hide instructions; see supply chain) | Run code |
| `templates/` | JSON/Markdown templates | Provide structure | Run code |
| `scripts/*.py` | Local Python, standard library only (`check_config.py` optionally uses PyYAML) | Read `radar-state.json`; write `radar.csv`, `radar.json`, `index.html`; validate | No network, no subprocess, no `eval`/`exec`, no deserialisation of untrusted objects (checked by `audit.sh`). `set_owner.py` rewrites text files in the repo and runs the sibling `build_bundle.py` in-process (`runpy`); it validates owner, repo and ref names against a strict pattern |
| `scripts/verify_deploy.py` | Maintainer smoke test | HTTP GET of your own repo's raw and Pages URLs | Anything else; not used during interviews |
| `scripts/serve_local.sh` | Optional helper that starts BYOR in Docker on your machine | Pull and run the upstream BYOR container, bound to `127.0.0.1`, data mounted read-only | Expose your radar to the LAN (fixed, §7); run without Docker |
| `config/tools.json`, `config/consortium-vocab.json`, `templates/consortium/` | Tool registry, closed vocabularies, round-kit and share-profile templates (consortium sharing, §16) | Run code | 
| `index.html` (root) | Landing page for GitHub Pages | Show instructions and a copy button | Anything beyond static display; no network calls except links |
| `examples/` | Fictional sample data and its generated outputs | Illustrate | Contain real data |
| `BUNDLE.md` | Generated single-file copy of everything, for clients that fetch one URL | Same as the files it concatenates | Differ from the repo (CI fails if stale) |
| Generated `radar-output/index.html` | The user's finished website | Display, filter, print; offer CSV/JSON download | Load external resources, send data, store cookies or use local storage. It carries a Content-Security-Policy that blocks everything except its own inline script (by hash) |

---

## 3. What using it enables, in plain terms

1. **The AI assistant learns what the user tells it** about software, owners, risk opinions and plans, within that conversation (and
   wherever the assistant vendor retains it).
2. **The user ends up holding a consolidated, readable record of the same information:** `radar-state.json`, CSV/JSON, and a website.
   That aggregation is more sensitive than any single fact in it (see §4).
3. **Optionally**, the user can publish that record to the internet, load it in a third-party hosted tool, or run BYOR locally.
4. Nothing in the skill set **needs** access to mail, files, calendars, CRMs, ticketing or cloud accounts. If the AI client has such
   connectors, the instructions forbid using them unless the user asks. Technical enforcement is the client's job, so disable them for this chat (§9).

---

## 4. Security model: trust boundaries and data flow

```
 ┌────────────┐  (1) instructions fetched    ┌──────────────────┐
 │ GitHub repo│ ───────────────────────────▶ │  AI client/agent │──(2) conversation──▶ AI vendor
 │ (public)   │      read-only, no data sent │  (your tenant)   │      (their data terms)
 └────────────┘                              └───────┬──────────┘
                                                     │ (3) files written locally
                                                     ▼
                         radar-state.json · radar.csv/json · index.html   (your device / workspace)
                                                     │
                                       (4) optional publication ▶ static host · Google Sheet · hosted/self-hosted BYOR
```

| Boundary | Trust assumption | Main risk | Where addressed |
|---|---|---|---|
| (1) Repo to client | You trust the repo owner and branch at the time of fetch | Tampered or malicious instructions | §5 T1, §9 (pin a commit, fork, review) |
| (2) Client to AI vendor | Conversation content is processed under your vendor agreement | Confidential data in third-party systems, retention, memory features, shared chats | §5 T4, §9 |
| (3) Local files | Your device/workspace security applies | Loss, over-sharing, unintended commit to a repo | `.gitignore` excludes radar data; §10 |
| (4) Publication | You decide who can see it | Public exposure of your technology map | §11 |

**Data sensitivity (what a radar can contain).**

| Content | Typical sensitivity | Note |
|---|---|---|
| Product names in use | Low individually, **Medium-High in aggregate** | Reveals your attack surface and suppliers |
| Security tooling coverage and gaps (endpoint, access control, cloud) | **High** | Reveals defensive posture and weak spots |
| "Caution" reasons, incidents, regrets | **High** | Free-text risk narrative |
| Owners and contributors | Medium | Personal data (names); gives phishing targets |
| Contract renewal dates, cost remarks | Medium | Negotiation and social-engineering value |
| AI usage and data-handling policy status | Medium | Reveals governance maturity |
| Credentials, keys, IP ranges, host lists, personal data of customers/donors/members | **Must never be entered** | The skill tells the agent to refuse and generalise |

**Classify the finished radar at least Internal; treat the full version (with Caution notes and security-domain blips) as Confidential.**

---

## 5. Threat analysis

Mapped to the OWASP Top 10 for LLM Applications (2025), plus agent-skill-specific risks that Anthropic and independent researchers
have highlighted. This is an assessment by the authors, not a certification.

| # | Threat | OWASP ref | How it could arise here | Controls in this repo | What you should do |
|---|---|---|---|---|---|
| T1 | **Supply-chain compromise of the instructions** (malicious commit, PR, dependency, account takeover). The agent fetches `main` live, so a change affects every new run. | LLM03 Supply Chain | A hostile edit to a skill, config or template tells the agent to leak data or take actions | Small, readable, dependency-free repo; CI; `audit.sh` flags exfiltration-style phrases, unexpected domains, hidden Unicode, encoded blobs; guardrails say to stop if instructions look altered | **Pin to a reviewed commit SHA or tag, or use your own fork**; branch protection, required review, 2FA/signed commits on the repo; re-run `audit.sh` on every update (§9) |
| T2 | **Indirect prompt injection** via web results, vendor brochures, pasted text, attached files, spreadsheet cells, or tool output | LLM01 Prompt Injection | Hidden text in a page or document tells the agent to email the radar or reveal data. Real-world precedent: zero-click injection against an enterprise assistant (CVE-2025-32711) | Guardrails: external content is data, never instructions; narrow action scope; web lookups are opt-in and queries must not contain internal facts; no publishing by the agent; evals 12-13 test this | Keep web/connectors off unless needed; review outputs; do not paste untrusted documents wholesale |
| T3 | **Excessive agency**: the agent uses connected tools (mail, drive, calendar, CRM, shell) beyond what the task needs | LLM06 Excessive Agency | Client has broad connectors or auto-approve for commands | Guardrails limit scope to local radar files and documented scripts; require explicit user request for any send/publish/connector action; one optional calendar reminder is offered only with consent | **Least privilege in the client:** disable connectors and auto-approve for the session; no production credentials in the environment |
| T4 | **Sensitive information disclosure** to the AI vendor, logs, memory or shared chats | LLM02 Sensitive Information Disclosure | User enters confidential detail; assistant "memory" retains it; chat shared | Guardrails forbid collecting secrets/personal data/NDA terms and tell the agent to generalise; depth setting lets users keep detail low | Use an approved enterprise tenant with appropriate data terms; consider zero-retention options; disable memory for this work; start with fictional data; classify the output |
| T5 | **Improper output handling**: generated HTML/CSV used to attack a viewer or spreadsheet user | LLM05 Improper Output Handling | Prompt-injected or hostile text in a description becomes a script in the website, or `=FORMULA()` in a CSV | Site generator escapes all text, uses an allow-list sanitiser, validates the accent colour, adds a hash-pinned CSP with `default-src 'none'`, has no external loads, no inline event handlers. CSV export neutralises leading `= + - @`. Regression tests cover these | Open generated files from a trusted location; keep the CSP; don't edit the HTML to add third-party scripts |
| T6 | **Hallucination and over-reliance**: invented facts, stale vendor info, overconfident ratings | LLM09 Misinformation | Model fills gaps; example tool lists age | User confirms every ring and description; facts are the user's own; public facts are source-tagged; example tools are "recall prompts, not recommendations", dated and alphabetical | Do not use the radar as an asset inventory, audit evidence or SBOM. Have an owner review before publication |
| T7 | **Public exposure of the radar** | n/a (data governance) | Public Google Sheet, public repo, public Pages site, shared link | Site is `noindex` by default; the agent runs a publishing gate and offers redaction; private hosting recommended | See §11. `noindex` is **not** access control |
| T8 | **Unbounded consumption** (cost/latency) | LLM10 Unbounded Consumption | Large bundle (~160 KB) and long interview consume tokens | Instructions load lazily; depth profiles cap questions and blips | Budget for it; prefer the lazy repo route to the bundle for metered usage |
| T9 | **Third-party component risk** (upstream BYOR, container image, hosted site) | LLM03 | `:latest` image changes; hosted tool reads your CSV from a URL | We do not bundle BYOR; `serve_local.sh` allows a pinned image digest and binds to localhost, read-only mount | Pin the image digest; review BYOR's privacy terms; self-host for sensitive radars |
| T10 | **Instruction/skill tampering in transit or at rest** | LLM03 | Mirror, proxy or edited copy | Absolute URL list in `AGENTS.md`; CI keeps bundle in sync; git history | Fetch from your own mirror over HTTPS; verify commit SHA in the URL |
| T11 | **Social engineering using the radar** | n/a | Attackers use the map for targeted phishing and vendor impersonation | Redaction offer; guidance to omit people and incident detail | Limit audience; avoid listing named individuals; brief the audience |

---

## 6. Controls built into the skill set

**Design (what the artefact is allowed to do)**
- No backend, accounts, secrets or telemetry; all outputs are local files.
- Scripts: standard library only; no network, process spawning, dynamic code execution or unsafe deserialisation.
- Generated website: self-contained, CSP with `default-src 'none'` and a script hash, no cookies/local storage/fetch, `noindex` by default, works without JavaScript.
- Least-privilege behaviour spelled out in `AGENTS.md` and `security-guardrails.md`: instruction hierarchy, action allow-list, publishing gate, redaction pass, secret and personal-data refusal, stop-if-tampered rule.

**Process (how we keep it that way)**
- `scripts/audit.sh`: scans for dangerous primitives, unexpected domains, exec-style instructions, hidden-instruction phrasing, zero-width/bidi Unicode, encoded blobs, and verifies the generated site is self-contained with a CSP.
- Automated tests (`tests/test_scripts.py`) include injection and escaping regression tests (script injection variants, meta-field escaping, CSP presence, colour validation, shell-safe env output, CSV formula neutralisation).
- CI runs config checks, tests and bundle freshness on every push.
- Behavioural evals (`evals/evals.json`) include prompt-injection, secret-handling and sensitive-detail scenarios.

---

## 7. Issues found and fixed during the pre-release security review

Transparency matters more than a clean record. These were found by the authors reviewing their own code before this release:

| Issue | Impact | Fix |
|---|---|---|
| Site description sanitiser left stray `<`, `>` characters unescaped | An unclosed tag such as `<script src=…` in a description could become a live script in the page | Rebuilt as placeholder-based allow-list: every tag is rebuilt or dropped, all remaining text is escaped; regression tests added |
| A FAQ field could be inserted unescaped when it started with `<` | Possible script injection through `how_to_nominate` | All FAQ text is escaped; test added |
| Accent colour inserted into CSS unvalidated | CSS injection via the CLI argument | Strict hex validation |
| No Content-Security-Policy on the generated site | No second line of defence | Hash-pinned CSP; inline event handler removed |
| `serve_local.sh` used `eval` on script output and published the port on all interfaces | A crafted quadrant name could inject shell; radar exposed to LAN | No `eval`; JSON passed as quoted variables; `--print-env` uses `shlex.quote`; port bound to `127.0.0.1`; data mounted read-only; image digest override |
| CSV could carry spreadsheet formulas | Formula injection when opened in Excel/Sheets | Leading `= + - @` neutralised in CSV; validator warns |

Known gap we have **not** closed: instructions are natural language, so no tool can prove an agent will obey them. Treat the guardrails as strong guidance plus tests, backed by client-side permissions, not a guarantee.

---

## 8. Verify it yourself (about 15 minutes)

```bash
git clone https://github.com/sl-stlzoo/byor-skill && cd byor-skill
git checkout <the tag or commit you intend to pin>

bash scripts/audit.sh                      # automated checks; read the output, do not only trust the exit code
pip install pyyaml pytest && pytest -q tests && python scripts/check_config.py

# Manual spot checks
grep -rnE "https?://" skills AGENTS.md config templates | sort -u | less      # every URL the agent could be pointed at
wc -c skills/*/SKILL.md AGENTS.md                                           # the whole instruction set is small enough to read
git log --stat --since="6 months ago"                                       # who changed what
```
Read `AGENTS.md` and `skills/byor-radar-builder/SKILL.md` end to end. If you adopt the repo, record the reviewed commit SHA.

---

## 9. Enterprise adoption guidance

**Recommended path**

1. **Fork or mirror** into your organisation. Enable branch protection, mandatory review, 2FA, signed commits, and a CODEOWNERS file for `skills/`, `config/`, `AGENTS.md`.
2. **Review** (§8) and record the commit SHA. Run `python scripts/set_owner.py YOUR_ORG REPO <commit-sha>` so every URL the agent fetches is pinned to that SHA, not a moving branch.
3. **Pilot** with fictional data (the `TESTING.md` protocol), then with a small team and low depth.
4. **Decide data rules**: what may be entered, how the output is classified, where it may be stored and published, who approves publication, retention period.
5. **Roll out** with the client settings below, and re-review on every upstream change (treat updates like any dependency upgrade).

**Client-side least-privilege settings (the controls that actually bind the agent)**

| Setting | Recommendation |
|---|---|
| Connectors/tools (mail, drive, calendar, CRM, ticketing, repos) | Disable for this chat/project |
| Command execution | Sandboxed workspace only; no production credentials or tokens in the environment; no auto-approve |
| Network access in the code sandbox | Off unless you need it |
| Web search/fetch | On only to fetch the pinned repo; off otherwise. If used for fact-checking, queries must be public product names only |
| Memory/personalisation | Off for this work |
| Data terms | Enterprise tenant with the retention and training terms your policy requires |
| Sharing of chats/projects | Restricted; review before sharing |
| Logging | Enable audit logs where the client offers them |

**Governance checklist**

| Control | Owner | When |
|---|---|---|
| Source review and SHA pin | Security / platform | Before pilot and each update |
| Data classification of radar outputs | CISO / data owner | Before pilot |
| Approved AI client and tenant | IT / procurement | Before pilot |
| Publication approval and hosting standard | CISO / comms | Before first publish |
| Redaction standard (owners, incidents, dates) | Security | Before first publish |
| Retention and deletion of state files and chats | Records / IT | At rollout |
| Review cadence for the radar and for this skill set | Radar owner | Quarterly or each edition |
| Incident path: what if a radar is published in error | Security | At rollout |

---

## 10. Best practices for end users

**Do**
- Start with a fictional run, then use real data at the lowest depth that is useful.
- Describe tools at product level. "We use X for helpdesk" is enough; skip versions, hostnames and configuration.
- Describe risk in general terms ("licence cost too high", "vendor changed direction"), not exploitable detail ("unpatched servers in …").
- Use roles for owners (for example "IT lead"), not personal names, unless the audience needs them.
- Review every description and ring before accepting it; you are the author and the AI is a scribe.
- Keep radar state, editions, outputs and consortium files in a managed, access-controlled location. `.gitignore` covers default local paths, not already-tracked files, custom names or forced additions; review `git status` before sharing.
- Ask for the redaction pass before sharing.
- Re-run `scripts/validate_radar.py` before loading anything into BYOR.

**Don't**
- Don't paste passwords, tokens, keys, IP ranges, host or vulnerability lists, customer, donor or member data, or NDA pricing.
- Don't let the AI browse the web, read your mail or connect to business systems for this task unless you explicitly want that.
- Don't paste vendor material or web pages you have not looked at; hidden text can carry instructions.
- Don't commit the radar files to a public repository, publish a public sheet, or enable public Pages without sign-off.
- Don't treat the radar as an asset inventory, audit evidence or a compliance artefact.
- Don't edit the generated site to add third-party scripts or trackers.

---

## 11. Publishing and exposure

| Route | Visibility | Risk | Guidance |
|---|---|---|---|
| Open `index.html` locally / attach to an email | Whoever receives it | Forwarding | Fine for small audiences; classify and label |
| Intranet / SSO-protected static hosting | Your staff | Low | **Recommended** for internal radars |
| Local or self-hosted BYOR (Docker) | Localhost or your network | Low; you operate the container | Pin the image digest; keep it behind your auth proxy |
| GitHub Pages | Public on most plans, even from a private repo | **High** | Use only for a radar you are content to publish. `noindex` stops polite crawlers, not people |
| Public Google Sheet or raw GitHub CSV (hosted BYOR) | Anyone with the link | **High** | Public by design; redact first |
| Private Google Sheet (hosted BYOR) | People you share with | Medium | Sheet sharing mistakes are common; review access |
| `radar.thoughtworks.com` hosted tool | The page runs in the viewer's browser and loads the file from the URL given | Third-party dependency | Review its privacy statement; self-host for anything sensitive |

The generated site embeds the whole radar and the CSV/JSON. Anyone who can load the page has the full dataset.

---

## 12. Privacy, licensing and compliance notes

- **Personal data:** the intended content is organisational, not personal. Contributor names and owners are optional; the agent asks before publishing names.
  The *wealth screening* domain touches fundraising privacy law (for example GDPR, CCPA); the skill only records product choices and policy status, never donor data.
- **No telemetry:** this repository collects nothing. Your AI vendor and hosting provider have their own logs.
- **Licences:** this repository is MIT. BYOR is AGPL-3.0 and is not included; if you modify and serve BYOR to others, AGPL obligations apply. The radar method is adapted from the Thoughtworks Technology Radar; the generated site carries an attribution and a non-affiliation note, uses none of their branding, and is not endorsed by Thoughtworks.
- **Compliance:** this is not a compliance tool. It has no SOC 2, ISO 27001 or similar attestation. Using it does not change your obligations under your frameworks; it can support, but not replace, a CMDB or asset inventory.

---

## 13. Assurance statement and limits

**What we assert:** the repository contains no network-capable code except the maintainer smoke test; no secrets; no telemetry; the generated site is self-contained with a restrictive CSP; the scripts use only the standard library; the checks in `scripts/audit.sh` pass; the regression tests pass; the issues in §7 were found and fixed before release.

**What we do not assert:** that any AI assistant will always follow the guardrails (models can be manipulated, and this is an open industry problem); that third-party tools it points to (BYOR, Docker images, hosting services, AI vendors) are secure; that this repository has been independently audited or penetration-tested. Independent review is welcome and we will credit reviewers.

**Industry context:** Anthropic's guidance on agent skills tells organisations to use skills only from trusted sources and to read a skill's instructions and any bundled code before use, and names prompt injection and data exfiltration as the main risks. Researchers have documented real incidents in public skill ecosystems and the lack of version pinning and inspection tooling. This repository is designed to be easy to inspect, pin and constrain for exactly those reasons.

---

## 14. Reporting a vulnerability

- **Please do not open a public issue.** Use GitHub's private vulnerability reporting for this repository (Security tab > Report a vulnerability), or contact the maintainers at the address in the repository profile.
- Include: affected file/version, impact, reproduction steps, and whether it is exploitable through an AI client, the scripts, the generated site, or the supply chain.
- **Targets (best effort, non-binding):** acknowledge within 3 business days, triage within 10, fix or mitigate critical issues within 30, and publish an advisory with credit (if wanted) after a fix is available.
- **Supported versions:** the latest tagged release and `main`.
- **Good-faith research** (testing your own copy or fork, no attacks on other people's data or infrastructure) will not be pursued.
- Prompt-injection or guardrail-bypass findings against a specific AI client are welcome, but may need to be reported to that client's vendor too.

---

## 15a. Consortium sharing (member side, v1; offline)

Optional Phase 11 lets a member contribute to a consortium round by producing a small, structured `contribution.json`. **Nothing is transmitted by the
skill set**: the user sends the file through the convener's agreed secure channel. Convener-side handling is in §15b.

| Threat | Control |
|---|---|
| Over-sharing (descriptions, owners, incidents, prices, people) | Allow-list export: only tool_id, domain, ring, experience bucket, scale, caution tags (and a 140-char rationale if named). Free text elsewhere is impossible by schema. Preview shows exactly what leaves; four explicit consent confirmations are required before export |
| Hostile or tampered files (prompt injection, markup, fake tools) | Strict validator: unknown keys, `< > ` ` `, URLs, `@`, bad vocab, wrong types, duplicate tools, unregistered tools, hash mismatch and kit mismatch are errors. Tags and buckets, not prose |
| Wrong-tool mapping silently skewing results | Canonical registry with aliases; fuzzy matches are suggestions only and need the user's yes; unresolved tools are excluded or marked custom |
| Re-identification of anonymous contributors | Coarse profile bands, `other` options, plan for a 3-organisation minimum cohort before any per-tool aggregate is shown (enforced in the convener tooling, next step); the convener always sees the name, and the skill says so |
| Irrevocability | Warned and confirmed before export; offline files cannot be recalled |
| Authenticity (who really sent it) | The hash is tamper evidence only, not a signature. Signed contributions are a planned later step; the convener should verify senders out of band |
| Legal exposure (confidentiality, competition law) | Skill tells users to involve counsel; format excludes prices, strategy and free-text vendor criticism |

## 15b. Consortium convener side (offline, v1)

The convener is the most sensitive role: they hold every raw contribution, including who sent what. The design keeps **scripts, not the AI, in contact with raw files**.

| Threat | Control |
|---|---|
| Hostile contribution files reaching an LLM (prompt injection, markup) | Raw files are read only by `aggregate_round.py` (strict validation, 1 MB cap, no network). The convener skill forbids opening or pasting them; the LLM sees only the intake report and `aggregate.json` |
| Re-identifying small groups or anonymous contributors | Hard floor of 3 organisations (no output at all below it; kit minimum cannot be set under 3); tools, domains, profile cells and tag counts below 3 are hidden or shown as `<k`; anonymous ratings join a tool's totals only when 3+ anonymous organisations used it, otherwise totals are named-only (tested: flipping anonymous ratings leaves the published data unchanged); slices need a k-anonymous basis |
| Leaking an anonymous name through narrative | `narrative.json` is validated: allow-listed keys, length caps, no markup/URLs/`@`, links only to benchmarked tools, and a deny-list of anonymous organisation names written by the aggregator |
| Forged, duplicated or stale senders | Roster check, newest-file-wins deduplication, hash and kit binding; the hash is tamper evidence not authenticity, so verify senders out of band |
| Output pages attacking readers | Benchmark site and member reports are static, escaped, `noindex`, no external loads, hash-pinned CSP, no inline handlers (tested) |
| Wrong recipient of a private report | One report per organisation, labelled private; skill instructs sending each only to its owner (a human process control) |
| Retention and breach | Convener-only folder (`_convener/`) is separated; charter template sets deletion dates and breach notice; checklist in `round-lifecycle.md` |
| Convener as concentration of trust | Inherent: the convener always sees raw data. Choose a trusted convener; keep the retained data minimal; delete on schedule |

| Two releases differing by one member revealing that member's change (differencing over time) | Trends use only the two published aggregates; adoption is rounded to 5-point steps; ring counts and per-organisation changes are never shown; a warning appears when the group changed a lot; the benchmark stays informal. This reduces but does not remove the risk with very small groups |
| Carrying data forward between rounds (member side) | `refresh_share_profile.py` copies only the member's own earlier choices; consent is reset to off every round; real-use answers that go backwards are flagged |

Residual: the rating normalisation (Adopt with under 6 months of use is counted as Trial, and so on) is a documented judgement, and the published count of reinterpreted ratings includes anonymous organisations in aggregate. An offline, non-signed exchange cannot prove who sent a file; treat this as an informal benchmark, not an audited dataset.

## 15. References

- OWASP GenAI Security Project, *Top 10 for LLM Applications 2025*: https://genai.owasp.org/llm-top-10/
- Anthropic, *Equipping agents for the real world with Agent Skills* (security considerations): https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- Anthropic, Agent Skills overview and security considerations: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- Li et al., *Towards Secure Agent Skills: Architecture, Threat Taxonomy, and Security Analysis* (arXiv): https://arxiv.org/abs/2604.02837
- Thoughtworks Build Your Own Radar: https://github.com/thoughtworks/build-your-own-radar and https://www.thoughtworks.com/radar/byor

*Change log:* v1.0 (14 Nov 2026) initial security review, hardening fixes (§7), `audit.sh`, guardrails, security tests.
