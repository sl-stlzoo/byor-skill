#!/usr/bin/env python3
"""Compare two consortium rounds from their aggregate.json files (stdlib only). Convener side.

  python scripts/compare_rounds.py old/aggregate.json new/aggregate.json [--registry config/tools.json] [--out round-output]
Writes trends.json and trends.md. Uses ONLY the two published (already anonymised, k-suppressed) aggregates; no raw files.
What it shows: adoption share change (rounded to 5-point steps), consensus ring change, tools that appeared or disappeared, domain coverage,
calibration shifts, and a comparability check. What it never shows: ring counts or per-organisation changes.
Members join and leave between rounds, so every result carries the group sizes and a warning when the groups differ a lot.
"""
import argparse, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import registry as R

STEP = 5


def r5(x): return int(round(x * 100 / STEP) * STEP)


def tools(agg, mig):
    out = {}
    for d, v in agg["domains"].items():
        for t in v["tools"]:
            tid = mig.get(t["tool_id"], t["tool_id"]); out[(d, tid)] = t
    return out


def compare(old, new, mig=None):
    mig = mig or {}
    ot, nt = tools(old, mig), tools(new, mig); k = new["round"]["min_cohort"]
    op, np_ = old["participants"], new["participants"]
    named_both = len(set(op["named"]) & set(np_["named"]))
    warns = []
    if old["round"]["rubric_version"] != new["round"]["rubric_version"]: warns.append("The rating rules (rubric) changed between rounds. Ring changes may not be real changes.")
    if old["round"]["registry_version"] != new["round"]["registry_version"]: warns.append("The tool list version changed. Merged tools were matched by the migration map." if mig else "The tool list version changed and no migration map was given. A renamed tool may look new.")
    declared = new["round"].get("previous_round_id") == old["round"]["id"]
    if not declared: warns.append("The new round's kit does not name the old round as its previous round.")
    size_shift = abs(np_["count"] - op["count"]) / max(1, op["count"])
    overlap = named_both / max(1, len(op["named"])) if op["named"] else 0
    confounded = size_shift > 0.25 or (op["named"] and overlap < 0.6)
    if confounded: warns.append("Different organisations took part this time. Treat changes as directional: they mix real change with who joined or left.")
    rising, falling, moved = [], [], []
    for key in sorted(set(ot) & set(nt)):
        a, b = ot[key], nt[key]; d_, tid = key
        da = r5(b["adoption_share"]) - r5(a["adoption_share"])
        row = {"tool_id": tid, "name": b["name"], "domain": d_, "adoption_before": r5(a["adoption_share"]), "adoption_now": r5(b["adoption_share"]), "change_points": da,
               "orgs_before": a["n_orgs"], "orgs_now": b["n_orgs"]}
        if da >= 10: rising.append(row)
        if da <= -10: falling.append(row)
        ca, cb = a.get("consensus"), b.get("consensus")
        if ca and cb and ca != cb: moved.append({"tool_id": tid, "name": b["name"], "domain": d_, "before": ca, "now": cb, "orgs_before": a["n_orgs"], "orgs_now": b["n_orgs"]})
    appeared = [{"tool_id": t, "name": nt[(d, t)]["name"], "domain": d, "orgs_now": nt[(d, t)]["n_orgs"]} for d, t in sorted(set(nt) - set(ot))]
    gone = [{"tool_id": t, "name": ot[(d, t)]["name"], "domain": d, "orgs_before": ot[(d, t)]["n_orgs"]} for d, t in sorted(set(ot) - set(nt))]
    od, nd = set(old["domains"]), set(new["domains"])
    cal = {}
    for f in new["calibration"]:
        a, b = old["calibration"].get(f, {}), new["calibration"][f]
        if all(isinstance(v, int) for v in list(a.values()) + list(b.values())) and a and b:
            ta, tb = max(a, key=a.get), max(b, key=b.get)
            if ta != tb: cal[f] = {"most_common_before": ta, "most_common_now": tb}
    return {"schema": "byor-consortium-trends/1", "old_round": {"id": old["round"]["id"], "title": old["round"]["title"], "organisations": op["count"]},
            "new_round": {"id": new["round"]["id"], "title": new["round"]["title"], "organisations": np_["count"]}, "min_cohort": k,
            "comparability": {"declared_follow_up": declared, "same_rating_rules": old["round"]["rubric_version"] == new["round"]["rubric_version"], "same_tool_list": old["round"]["registry_version"] == new["round"]["registry_version"],
                              "named_in_both_rounds": named_both, "domains_in_both": len(od & nd), "domains_only_before": sorted(od - nd), "domains_only_now": sorted(nd - od), "confounded": bool(confounded), "warnings": warns},
            "rising": sorted(rising, key=lambda x: -x["change_points"]), "falling": sorted(falling, key=lambda x: x["change_points"]), "consensus_moved": moved,
            "appeared": appeared, "no_longer_shown": gone, "calibration_shift": cal, "panel": None}


def to_markdown(t):
    L = [f"# Trends: {t['old_round']['title']} to {t['new_round']['title']}", "", f"{t['old_round']['organisations']} organisations before, {t['new_round']['organisations']} now. Adoption shown in steps of {STEP} points.", ""]
    L += [f"**Warning:** {w}" for w in t["comparability"]["warnings"]] + [""] if t["comparability"]["warnings"] else []
    for title, rows, fmt in (("Rising adoption", t["rising"], lambda x: f"{x['name']}: {x['adoption_before']}% to {x['adoption_now']}% ({x['change_points']:+d} points)"),
                             ("Falling adoption", t["falling"], lambda x: f"{x['name']}: {x['adoption_before']}% to {x['adoption_now']}% ({x['change_points']:+d} points)"),
                             ("Peer rating moved", t["consensus_moved"], lambda x: f"{x['name']}: {x['before']} to {x['now']}"),
                             ("New in the benchmark", t["appeared"], lambda x: f"{x['name']} ({x['orgs_now']} organisations)"), ("No longer shown", t["no_longer_shown"], lambda x: f"{x['name']} ({x['orgs_before']} organisations before)")):
        if rows: L += [f"## {title}"] + [f"- {fmt(x)}" for x in rows] + [""]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("old"); ap.add_argument("new"); ap.add_argument("--registry"); ap.add_argument("--out", default="round-output"); a = ap.parse_args()
    ld = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    old, new = ld(a.old), ld(a.new)
    for x in (old, new):
        if x.get("schema") != "byor-consortium-aggregate/1": sys.exit("Not an aggregate.json file.")
    rp = pathlib.Path(a.registry) if a.registry else R.DEFAULT
    mig = R.migration_map(json.loads(rp.read_text(encoding="utf-8"))) if rp.exists() else {}
    t = compare(old, new, mig); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "trends.json").write_text(json.dumps(t, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"); (out / "trends.md").write_text(to_markdown(t), encoding="utf-8"); print(to_markdown(t))


if __name__ == "__main__":
    main()
