#!/usr/bin/env python3
"""Convert radar-state.json into BYOR-ready CSV and JSON.   (stdlib only)

Usage:
  python scripts/state_to_radar.py radar-state.json                  # writes radar-output/radar.csv + radar.json
  python scripts/state_to_radar.py radar-state.json --compat         # map quadrants to BYOR default names (hosted site)
  python scripts/state_to_radar.py radar-state.json --full           # extra columns: domain, owner, confidence, last_reviewed
  python scripts/state_to_radar.py radar-state.json --print-env      # print RINGS/QUADRANTS for a self-hosted BYOR
  python scripts/state_to_radar.py radar-state.json --hold-label Caution
"""
import argparse, csv, json, os, shlex, sys

DEFAULT_Q = ["techniques", "platforms", "tools", "languages & frameworks"]
DEFAULT_RING_NAMES = {"adopt": "Adopt", "trial": "Trial", "assess": "Assess", "hold": "Caution"}


def neutralise(row):
    """CSV/formula-injection guard: cells starting with = + - @ tab or CR get a leading apostrophe (spreadsheet apps then show text)."""
    return {k: ("'" + v if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r") else v) for k, v in row.items()}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def ring_name(state, ring_id, hold_label):
    for r in state.get("rings", []):
        if r["id"] == ring_id:
            if ring_id == "hold":
                return hold_label or r.get("name") or "Caution"
            return r["name"]
    return DEFAULT_RING_NAMES.get(ring_id, ring_id)


def build_rows(state, compat=False, full=False, hold_label=None):
    hold_label = hold_label or state.get("meta", {}).get("hold_label", "Caution")
    quads = state["quadrants"]
    qname = {q["id"]: q["name"] for q in quads}
    qindex = {q["id"]: i for i, q in enumerate(quads)}
    has_status = any(b.get("status") for b in state["blips"])
    rows = []
    for b in state["blips"]:
        qn = qname.get(b["quadrant"], b["quadrant"])
        desc = (b.get("description") or "").strip()
        if compat:
            i = qindex.get(b["quadrant"], 0)
            desc = f"<b>{qn}</b>: {desc}"
            qn = DEFAULT_Q[i] if i < 4 else DEFAULT_Q[0]
        row = {
            "name": b["name"].strip(),
            "ring": ring_name(state, b["ring"], hold_label),
            "quadrant": qn,
            "isNew": "TRUE" if b.get("isNew") else "FALSE",
            "description": desc,
        }
        if has_status:
            row["status"] = b.get("status") or ""
        if full:
            row.update({"domain": b.get("domain", ""), "owner": b.get("owner", ""),
                        "confidence": b.get("confidence", ""), "last_reviewed": b.get("last_reviewed", "")})
        rows.append(row)
    # stable order: quadrant order, then ring order, then name
    rorder = {"adopt": 0, "trial": 1, "assess": 2, "hold": 3, "caution": 3}
    qorder = {n: i for i, n in enumerate(qname.values())}
    rows.sort(key=lambda r: (qorder.get(r["quadrant"], 99), rorder.get(r["ring"].lower(), 9), r["name"].lower()))
    return rows


def env_strings(state, hold_label=None):
    hold_label = hold_label or state.get("meta", {}).get("hold_label", "Caution")
    rings = [ring_name(state, r["id"], hold_label) for r in state["rings"]]
    quads = [q["name"] for q in state["quadrants"]]
    return json.dumps(rings), json.dumps(quads)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("state")
    ap.add_argument("--out", default=None, help="output directory (default: radar-output next to state file)")
    ap.add_argument("--compat", action="store_true", help="rename quadrants to BYOR defaults for radar.thoughtworks.com")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--hold-label", choices=["Hold", "Caution"], help="name of the 4th ring (default Caution)")
    ap.add_argument("--print-env", action="store_true")
    ap.add_argument("--print-rings-json", action="store_true")
    ap.add_argument("--print-quadrants-json", action="store_true")
    a = ap.parse_args()

    state = load(a.state)
    if a.print_env:
        r, q = env_strings(state, a.hold_label)
        print(f"export RINGS={shlex.quote(r)}")
        print(f"export QUADRANTS={shlex.quote(q)}")
        return
    if a.print_rings_json or a.print_quadrants_json:
        r, q = env_strings(state, a.hold_label)
        print(r if a.print_rings_json else q)
        return
    rows = build_rows(state, a.compat, a.full, a.hold_label)
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.state)), "radar-output")
    os.makedirs(out, exist_ok=True)
    cols = list(rows[0].keys()) if rows else ["name", "ring", "quadrant", "isNew", "description"]
    with open(os.path.join(out, "radar.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_MINIMAL)
        w.writeheader(); w.writerows(neutralise(r) for r in rows)
    with open(os.path.join(out, "radar.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(rows)} blips -> {out}/radar.csv and radar.json" + (" (compat names)" if a.compat else ""))


if __name__ == "__main__":
    sys.exit(main())
