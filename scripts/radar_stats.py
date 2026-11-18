#!/usr/bin/env python3
"""Progress and coverage report from radar-state.json (used for the progress footer and quadrant checkpoints).
Usage: python scripts/radar_stats.py radar-state.json [--quadrant business-ops]
"""
import argparse, json, collections

ap = argparse.ArgumentParser()
ap.add_argument("state"); ap.add_argument("--quadrant")
a = ap.parse_args()
s = json.load(open(a.state, encoding="utf-8"))
doms = s["domains"]
active = {k: v for k, v in doms.items() if v.get("status") != "skipped"}
done = [k for k, v in active.items() if v["status"] == "done"]
print(f"Overall: {len(done)}/{len(active)} domains done ({round(100*len(done)/max(1,len(active)))}%), {len(s['blips'])} blips")
for q in s["quadrants"]:
    ds = [k for k, v in active.items() if v.get("quadrant") == q["id"]]
    dn = [k for k in ds if active[k]["status"] == "done"]
    bl = [b for b in s["blips"] if b["quadrant"] == q["id"]]
    rc = collections.Counter(b["ring"] for b in bl)
    print(f"- {q['name']}: {len(dn)}/{len(ds)} domains, {len(bl)} blips, rings {dict(rc)}")
    if a.quadrant == q["id"]:
        for k in ds: print(f"    {k}: {active[k]['status']}")
nxt = [k for k, v in active.items() if v["status"] in ("pending", "in_progress")]
print("Next up:", nxt[0] if nxt else "none, ready for calibration")
