#!/usr/bin/env python3
"""Finish an edition: fill in what changed, then save a snapshot (stdlib only).

  python scripts/freeze_edition.py radar-state.json [--edition 2027-H1] [--keep 4] [--dir editions] [--force]

1. Names the edition (half-yearly by default: 2027-H1 for Jan-Jun, 2027-H2 for Jul-Dec).
2. If an earlier edition exists, sets each tool's status automatically (New, Moved In, Moved Out, No Change) and isNew,
   and records previous_ring. First edition: statuses are left as they are.
3. Saves editions/<id>.json and editions/index.json. Keeps the newest 4 snapshots (3 previous + current) and deletes older ones.
Refuses to overwrite an existing snapshot unless --force.
"""
import argparse, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import compare_editions as C


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("state"); ap.add_argument("--edition"); ap.add_argument("--keep", type=int, default=4); ap.add_argument("--dir"); ap.add_argument("--force", action="store_true")
    a = ap.parse_args(); sp = pathlib.Path(a.state); s = json.loads(sp.read_text(encoding="utf-8"))
    eid = a.edition or s["meta"].get("edition") or C.edition_id()
    if not re.fullmatch(r"\d{4}-H[12]|\d{4}-[A-Za-z0-9-]{1,12}", eid): sys.exit("Edition id looks like 2027-H1.")
    s["meta"]["edition"] = eid; edir = pathlib.Path(a.dir or sp.resolve().parent / "editions"); edir.mkdir(parents=True, exist_ok=True)
    target = edir / f"{eid}.json"
    if target.exists() and not a.force: sys.exit(f"{target.name} already exists. Use --force to replace it.")
    pid, pp = C.find_previous(sp, eid, edir)
    if pp:
        prev = json.loads(pp.read_text(encoding="utf-8")); prev["meta"].setdefault("edition", pid); pi = C.index(prev)
        for b in s["blips"]:
            p = pi.get(C.key(b)) or pi.get("n:" + C.norm(b["name"]))
            if not p: b["status"], b["isNew"] = "New", True; continue
            d = C.RANK[b["ring"]] - C.RANK[p["ring"]]; b["isNew"] = False; b["previous_ring"] = p["ring"]
            b["status"] = "Moved In" if d < 0 else "Moved Out" if d > 0 else "No Change"
        s["meta"]["previous_edition"] = pid
    sp.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    target.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ids = sorted(p.stem for p in edir.glob("*.json") if p.stem != "index"); removed = []
    for old in ids[:-a.keep] if a.keep > 0 else []: (edir / f"{old}.json").unlink(); removed.append(old)
    ids = [i for i in ids if i not in removed]
    (edir / "index.json").write_text(json.dumps({"editions": [{"id": i, "tools": len(json.loads((edir / f"{i}.json").read_text(encoding="utf-8"))["blips"])} for i in ids]}, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {target}" + (f"; marked changes since {pid}" if pp else "; first edition, no earlier one to compare") + (f"; removed older snapshots: {', '.join(removed)}" if removed else ""))


if __name__ == "__main__":
    main()
