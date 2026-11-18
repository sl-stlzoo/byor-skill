#!/usr/bin/env python3
"""Convener-side intake and privacy-preserving aggregation for a consortium round.  (stdlib only, deterministic, no network)

  python scripts/aggregate_round.py --kit round-kit.json --inbox inbox/ [--roster roster.json] [--out round-output] [--allow-unlisted]

Raw contribution files are read ONLY by this script (never by an LLM). Outputs:
  <out>/aggregate.json            members-safe: anonymised, k-suppressed. This is the only data the benchmark site and any narrative use.
  <out>/_convener/intake-report.md and .json   CONVENER ONLY: accepted / rejected / superseded files and reasons
  <out>/_convener/anon-names.json              CONVENER ONLY: names to keep out of any narrative (anonymous contributors)
Exit codes: 0 ok; 1 usage or kit error; 2 fewer than min_cohort accepted contributions (no aggregates written).

Privacy rules (k = kit.min_cohort, never below 3):
  * No aggregate at all below k accepted organisations.
  * A tool is shown only if >= k distinct organisations used it; a domain only if >= k organisations covered it.
  * Differencing guard: anonymous contributors enter a tool's totals only when at least k anonymous organisations used that tool;
    otherwise totals are computed over named organisations only (basis "named-only") so an anonymous rating can never be derived by
    subtraction. Named organisations' own ratings are always shown (they consented). Tag and profile cells with fewer than k show "<k".
  * Anonymous contributors are never named; the convener (who holds the files) can always see them.
Rating normalisation (rubric v1, evidence-aware): adopt with < 6 months real use -> trial; trial with no real use -> assess. Raw rings are kept
and the number of adjusted ratings is reported.
"""
import argparse, collections, datetime, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import registry as R
import validate_contribution as V

RING_ORDER = ["adopt", "trial", "assess", "caution"]
EXP_ORDER = V.VOCAB["experience"]
MAX_FILE = 1_000_000
RULES = ["Adopt with under 6 months of real use is counted as Trial.", "Trial with no real use is counted as Assess.",
         "Tools used by fewer than the minimum cohort of organisations are not shown.",
         "Anonymous ratings are included in a tool's totals only when at least the minimum cohort of anonymous organisations used it; otherwise totals cover named organisations only."]


def org_key(n): return re.sub(r"[^a-z0-9]+", "", (n or "").lower())


def effective(ring, exp):
    adjusted = False
    if ring == "adopt" and exp in ("none", "lt-6m"): ring, adjusted = "trial", True
    if ring == "trial" and exp == "none": ring, adjusted = "assess", True
    return ring, adjusted


def cell(n, k): return n if n >= k else "<k"


def basis_rows(rows, k):
    """Rows used for totals. Anonymous rows count only if >= k anonymous orgs (k-anonymous group); else named-only."""
    a = sum(r["anon"] for r in rows)
    return (rows, "all") if a == 0 or a >= k else ([r for r in rows if not r["anon"]], "named-only")


def tool_name(reg, tid):
    return reg.tools[tid]["name"] if tid in reg.tools else tid[2:].replace("-", " ").title() + " (custom)"


def intake(kit, inbox, roster, allow_unlisted, reg):
    results, accepted = [], {}
    listed = {org_key(o["org_name"]) for o in (roster or {}).get("orgs", [])}
    for p in sorted(pathlib.Path(inbox).glob("*")):
        if not p.is_file(): continue
        rec = {"file": p.name, "status": "rejected", "reasons": []}; results.append(rec)
        if p.suffix.lower() != ".json": rec["reasons"].append("not a .json file"); continue
        if p.stat().st_size > MAX_FILE: rec["reasons"].append("file too large"); continue
        try: c = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e: rec["reasons"].append(f"unreadable JSON: {e}"); continue
        E, W = V.validate(c, kit, reg)
        if E: rec["reasons"] += E[:12]; continue
        key = org_key(c["contributor"]["org_name"]); rec["org"] = c["contributor"]["org_name"]; rec["attribution"] = c["contributor"]["attribution"]; rec["warnings"] = W
        if roster is not None and not allow_unlisted and key not in listed: rec["reasons"].append("organisation is not on the roster"); continue
        prev = accepted.get(key)
        if prev and (prev["c"]["generated"], prev["rec"]["file"]) >= (c["generated"], p.name):
            rec["status"] = "superseded"; rec["reasons"].append(f"newer or equal contribution from this organisation already accepted ({prev['rec']['file']})"); continue
        if prev: prev["rec"]["status"] = "superseded"; prev["rec"]["reasons"].append(f"replaced by newer file {p.name}")
        rec["status"] = "accepted"; accepted[key] = {"c": c, "rec": rec}
    return results, [v["c"] for v in accepted.values()]


def aggregate(kit, contribs, reg):
    k = kit["min_cohort"]; N = len(contribs); named = sorted(c["contributor"]["org_name"] for c in contribs if c["contributor"]["attribution"] == "named")
    anon = N - len(named); adjusted = 0
    comp = {d: collections.Counter(c["contributor"]["profile"][d] for c in contribs) for d in ("sector", "size_band", "region")}
    calib = {f: collections.Counter(str(c["calibration"][f]) for c in contribs) for f in V.VOCAB["calibration"]}
    covering = collections.defaultdict(list)
    by_tool = collections.defaultdict(list)                                   # (domain, tool_id) -> rows
    for c in contribs:
        for d in c["domains_covered"]: covering[d].append(c)
        org = c["contributor"]; 
        for b in c["blips"]:
            ring, adj = effective(b["ring"], b["experience"]); adjusted += adj
            by_tool[(b["domain"], b["tool_id"])].append({"org": org["org_name"], "anon": org["attribution"] == "anonymous", "profile": org["profile"], "raw": b["ring"], "ring": ring,
                                                         "experience": b["experience"], "scale": b["scale"], "tags": b.get("caution_tags", []), "rationale": b.get("rationale", "")})
    domains = {}
    for d in kit["domains"]:
        cov = len(covering[d]); entry = {"orgs_covering": cov if cov >= k else "<k", "suppressed": cov < k, "tools": [], "long_tail_suppressed": 0}
        domains[d] = entry
        if cov < k: continue
        for (dom, tid), rows in sorted(by_tool.items()):
            if dom != d: continue
            n = len(rows)
            if n < k: entry["long_tail_suppressed"] += 1; continue
            brows, basis = basis_rows(rows, k)
            t = {"tool_id": tid, "name": tool_name(reg, tid), "licence": reg.tools.get(tid, {}).get("licence", "unknown"), "n_orgs": n, "adoption_share": round(n / cov, 2),
                 "named_ratings": sorted([{"org": r["org"], "ring": r["ring"], "experience": r["experience"], "scale": r["scale"], **({"rationale": r["rationale"]} if r["rationale"] else {})} for r in rows if not r["anon"]], key=lambda x: x["org"].lower()),
                 "basis": basis, "n_basis": len(brows)}
            if brows:
                nb = len(brows); rc = collections.Counter(r["ring"] for r in brows); top = max(rc.values()); modes = [x for x in RING_ORDER if rc[x] == top]
                tags = collections.Counter(t_ for r in brows for t_ in r["tags"])
                t.update({"ring_counts": {x: rc.get(x, 0) for x in RING_ORDER}, "consensus": modes[0] if len(modes) == 1 else "split", "consensus_rings": modes, "agreement": round(top / nb, 2),
                          "experience_counts": {x: sum(1 for r in brows if r["experience"] == x) for x in EXP_ORDER}, "scale_counts": {x: sum(1 for r in brows if r["scale"] == x) for x in V.VOCAB["scale"]},
                          "caution_tags": {tg: c_ for tg, c_ in sorted(tags.items()) if c_ >= k}})
                flags = []
                if t["agreement"] < 0.6 and nb >= 3: flags.append("contested")
                if rc["caution"] / nb >= 1 / 3 and nb >= 3: flags.append("caution-watch")
                if sum(1 for r in brows if r["experience"] in ("none", "lt-6m")) / nb >= 0.6 and nb >= 3: flags.append("emerging")
                t["flags"] = flags
            entry["tools"].append(t)
        entry["tools"].sort(key=lambda t: (-t["n_orgs"], t["name"].lower()))
    slices = {}
    for dim in ("sector", "region"):
        out = {}
        for val, cnt in comp[dim].items():
            if cnt < k: continue
            tools = []
            for (dom, tid), rows in sorted(by_tool.items()):
                sub = [r for r in rows if r["profile"][dim] == val]
                bsub, _ = basis_rows(sub, k)
                if len(sub) >= k and len(bsub) >= k:
                    rc = collections.Counter(r["ring"] for r in bsub); top = max(rc.values()); modes = [x for x in RING_ORDER if rc[x] == top]
                    tools.append({"tool_id": tid, "name": tool_name(reg, tid), "domain": dom, "n_orgs": len(sub), "consensus": modes[0] if len(modes) == 1 else "split"})
            out[val] = {"orgs": cnt, "tools": sorted(tools, key=lambda t: (-t["n_orgs"], t["name"].lower()))}
        slices[dim] = out
    return {"schema": "byor-consortium-aggregate/1",
            "round": {"id": kit["round_id"], "title": kit["title"], "convener": kit["convener"], "registry_version": kit["registry_version"], "rubric_version": kit["rubric_version"], "min_cohort": k, "generated": datetime.date.today().isoformat(), **({"previous_round_id": kit["previous_round_id"]} if "previous_round_id" in kit else {}), **({"sequence": kit["sequence"]} if "sequence" in kit else {})},
            "participants": {"count": N, "named": named, "anonymous_count": anon, "composition": {d: {v: cell(n, k) for v, n in sorted(cn.items())} for d, cn in comp.items()}},
            "calibration": {f: {v: cell(n, k) for v, n in sorted(cn.items())} for f, cn in calib.items()},
            "normalisation": {"adjusted_ratings": adjusted, "rules": RULES}, "domains": domains, "slices": slices}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--kit", required=True); ap.add_argument("--inbox", required=True); ap.add_argument("--roster")
    ap.add_argument("--out", default="round-output"); ap.add_argument("--allow-unlisted", action="store_true"); ap.add_argument("--registry")
    a = ap.parse_args()
    try: kit = json.loads(pathlib.Path(a.kit).read_text(encoding="utf-8")); roster = json.loads(pathlib.Path(a.roster).read_text(encoding="utf-8")) if a.roster else None
    except Exception as e: sys.exit(f"Cannot read kit/roster: {e}")
    E, _ = V.validate_kit(kit)
    if E: sys.exit("Kit invalid:\n  " + "\n  ".join(E))
    reg = R.load(a.registry); results, contribs = intake(kit, a.inbox, roster, a.allow_unlisted, reg)
    out = pathlib.Path(a.out); conv = out / "_convener"; conv.mkdir(parents=True, exist_ok=True)
    (conv / "intake-report.json").write_text(json.dumps({"generated": datetime.date.today().isoformat(), "min_cohort": kit["min_cohort"], "files": results}, indent=2) + "\n", encoding="utf-8")
    md = [f"# Intake report: {kit['title']}  (CONVENER ONLY)", "", f"Accepted: {len(contribs)} | min cohort: {kit['min_cohort']}", "", "| File | Organisation | Attribution | Status | Notes |", "|---|---|---|---|---|"]
    for r in results: md.append(f"| {r['file']} | {r.get('org', '')} | {r.get('attribution', '')} | {r['status']} | {'; '.join(r['reasons'] + r.get('warnings', []))[:300]} |")
    (conv / "intake-report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Intake: {len(contribs)} accepted, {sum(r['status'] == 'rejected' for r in results)} rejected, {sum(r['status'] == 'superseded' for r in results)} superseded. See {conv}/intake-report.md")
    if len(contribs) < kit["min_cohort"]:
        print(f"Only {len(contribs)} accepted; the minimum cohort is {kit['min_cohort']}. No aggregates written."); return 2
    (conv / "anon-names.json").write_text(json.dumps(sorted(c["contributor"]["org_name"] for c in contribs if c["contributor"]["attribution"] == "anonymous")) + "\n", encoding="utf-8")
    agg = aggregate(kit, contribs, reg); (out / "aggregate.json").write_text(json.dumps(agg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    shown = sum(len(d["tools"]) for d in agg["domains"].values())
    print(f"Wrote {out}/aggregate.json: {agg['participants']['count']} organisations, {shown} tools shown, {sum(d['long_tail_suppressed'] for d in agg['domains'].values())} suppressed (<{kit['min_cohort']}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
