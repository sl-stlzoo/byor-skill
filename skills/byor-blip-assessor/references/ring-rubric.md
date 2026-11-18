# Ring rubric

Defaults live in `config/rings.yaml` (paraphrased from the canonical Thoughtworks Technology Radar FAQ); Phase 4 tailors
them. This file explains how to apply them consistently. Principles: `byor-radar-builder/references/canonical-radar-principles.md`.

## Decision grid

| Ring | Question to answer "yes" | Typical evidence | Typical next action |
|---|---|---|---|
| **Adopt** | "Would it be a poor, even irresponsible, choice NOT to use this where it fits?" | 6+ months production, owner named, risks reviewed, exit known | Standardise, train, renew |
| **Trial** | "Have we used it for real work, in a limited way, and do we want to learn more?" | Real use in one team/site; success measures | Expand carefully, set exit criteria |
| **Assess** | "Is it interesting enough to look at closely and keep an eye on?" | Demo, reference call, request | Proof of concept, budget check |
| **Caution** | "Have we had a bad experience, or do we see risk, so that others should consider alternatives or avoid it?" | Incidents, EOL, poor fit, adverse vendor change, misuse | Avoid new use, educate, plan to move away |

## Rules of thumb (from the canonical radar, adapted)
1. **Trial needs real experience.** A demo, sandbox or "we looked at the website" is Assess. This is why a radar can lag
   behind the technology curve, and that is fine.
2. **Adopt is a high bar and always contextual.** It does not mean "use everywhere"; it means "proven and mature, and
   not using it where it fits would be a poor choice".
3. **Caution is about experience, not fashion.** It can apply to something widely accepted, to a tool that is fine but
   misused, or to something already in use that deserves a rethink. It is not a synonym for "old".
4. **Rings spark the arguments; quadrants do not.** Spend the discussion time on rings. Which quadrant a blip is in
   matters little.
5. **Position inside a ring is meaningful.** Closer to the inner edge = more confident (a Trial blip near Adopt is
   rising). Capture this as optional `radial` (0 = innermost edge of the ring, 1 = outermost). Ask only at standard/deep depth:
   "Within Trial, is this close to Adopt, or only just in?" Angle within a quadrant carries no meaning.
6. **Blips are in motion.** The default is that a blip stays on the radar for one edition unless it moves or something
   noteworthy happened. Settled tools you are happy with may deliberately be absent (the first edition is the exception:
   record the current state of the portfolio).
7. **Keep the radar readable.** If it is crowded, cut, often by a vote. Prefer fewer, better-described blips.

## Evidence challenge (use when ratings look inflated)
Pick up to three Adopt blips and ask: owner? renewal date? what happens if the vendor disappears? Anything that fails
two of three moves to Trial unless the user insists (record `decision_notes: "user override"`).
Also challenge Trial items that are really only demos: "Has real work run through it?" If not, Assess.

## Open source vs commercial: apply the same bar
- Open source: also ask who maintains it (community size, release cadence, commercial backer), how security patches
  reach you, and who in the organisation can run or support it.
- Commercial/SaaS: also ask about data export, contract term and price-rise exposure, sub-processors/residency.
- Neither is better in itself; record what the user told you.

## Per-domain `lens` shortcuts
Each domain in `config/domains.yaml` has a `lens` list. Pick the one or two items most relevant and mention them in the
watch-out sentence.

## Calibration sanity ranges (soft guidance, not rules)
Adopt 30-50%, Trial 15-25%, Assess 15-30%, Caution 5-20%. If Caution is empty, the radar is probably missing what to
avoid; ask. If Assess dominates it may be a wish list; ask which are truly planned.
