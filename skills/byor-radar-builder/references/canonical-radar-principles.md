# Canonical radar principles (what this skill set must exemplify)

Sources (read, then paraphrased here; never copy their text into user deliverables):
- https://www.thoughtworks.com/radar/faq  (rationale and rules)
- https://www.thoughtworks.com/radar  (structure of the published radar page)
- https://www.thoughtworks.com/radar/byor  (build your own)

## Rationale (from the FAQ) and how this repo honours it

| Canonical principle | What the agent and the site do |
|---|---|
| A radar is an **opinionated snapshot** of experience, not a survey of the market; no attempt to be comprehensive | Intro and FAQ on the site say so; the agent never pads the radar with tools nobody has experience of |
| **Not a vendor-influenced list**; no revenue motive | Neutral tone, seeds are recall prompts, no promotion; site footer states it is an opinion |
| **Blips** = tools, techniques, platforms, languages/frameworks, in motion | Blips may also be techniques/practices (e.g. "Single sign-on everywhere") |
| **Two axes:** quadrants (kind) and rings (recommendation); quadrants matter little, rings matter a lot | Phase 3 is light; Phases 4, 5, 6 spend the effort on rings |
| Rings: Adopt, Trial, Assess, **Caution** (4th ring) | `config/rings.yaml`; `hold` data value still accepted |
| **Trial only with real experience; Adopt only when not using it would be a poor choice** | Rubric rules of thumb; evidence challenge |
| **Radial position matters, angle does not** | Optional `radial` field; site draws it, never implies meaning for angle |
| Blips **appear for one edition** unless they move or something noteworthy happens; archive is not updated | `status` column (New / Moved in / Moved out / No change), maintenance phase, archive advice |
| **Crowdsourced nominations**, then debate; each blip has a **champion** who writes it up | Interview gathers nominations; `champion`/`owner` per blip; site FAQ says how to nominate |
| Radar is **not an approved-technology list** | Intro and FAQ |
| Published as an **interactive site and a read-everything PDF** | Single-page site with filter/zoom, all-blips section, print-to-PDF styles, CSV/JSON download |
| **Themes** summarise patterns across blips (3 to 4, titled, each links to blips, mentions cautions and what to expect next) | Phase 7 narrative workshop; site "Themes for this edition" |
| **How to keep up:** read Adopt, then Caution, then Trial, then Assess | Site "Keeping up" list |
| **Contributors** and process are public | Contributors list, methodology FAQ, review cadence |
| Twice-yearly cadence | Cadence recorded in Phase 10; "next review" shown on the site |

## Structure of the canonical radar page (the site's skeleton)
1. Edition label and date, title, one-line tagline
2. One-paragraph intro of what the radar is
3. Interactive radar with four quadrants, four rings, legend (new / moved in-out / no change), per-quadrant lists
4. Plain definitions of the rings
5. Download (PDF) and subscribe/stay informed
6. **Themes for this edition**: titled sections, each a short essay linking to blips, naming what is emerging, what to be
   cautious about, and what we expect next
7. Featured insights (here: decisions and actions)
8. Contributors, archive, FAQ

## Theme writing pattern (Phase 7)
Each theme: (1) the pattern in one sentence, (2) 2-4 linked blips as evidence, (3) a nuance or tension, (4) a caution if
there is one ("we caution against ..."), (5) what we expect in the coming months. 90-180 words. Evidence only from
the user's answers.
