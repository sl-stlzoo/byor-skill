#!/usr/bin/env python3
"""Compare two radar editions (stdlib only). Used by freeze_edition.py and build_site.py.

  python scripts/compare_editions.py [radar-state.json] [--previous editions/2026-h2.json] [--out radar-output]
Finds the previous edition in ./editions next to the state file (newest id below the current one) unless --previous is given.
Writes changes.json and changes.md. Read-only on your radar files.
Tools are matched by tool_id when both sides have one, else by normalised name.
"""
import argparse, datetime, json, pathlib, re, sys

RANK = {"adopt": 0, "trial": 1, "assess": 2, "hold": 3, "caution": 3}
LABEL = {"adopt": "Adopt", "trial": "Trial", "assess": "Assess", "hold": "Caution", "caution": "Caution"}


def edition_id(d=None):
    d = d or datetime.date.today(); return f"{d.year}-H{1 if d.month <= 6 else 2}"


def norm(s): return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()
def key(b): return b.get("tool_id") or "n:" + norm(b["name"])


def index(state):
    out = {}
    for b in state["blips"]:
        out.setdefault(key(b), b)
        out.setdefault("n:" + norm(b["name"]), b)          # name fallback so a missing tool_id on one side still matches
    return out


def find_previous(state_path, current_id, edir=None):
    edir = pathlib.Path(edir or pathlib.Path(state_path).resolve().parent / "editions")
    if not edir.is_dir(): return None, None
    ids = sorted(p.stem for p in edir.glob("*.json") if p.stem != "index" and p.stem < current_id)
    return (ids[-1], edir / f"{ids[-1]}.json") if ids else (None, None)


def load_all(edir):
    edir = pathlib.Path(edir)
    snaps = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(edir.glob("*.json")) if p.stem != "index"} if edir.is_dir() else {}
    return snaps


def compare(prev, cur, today=None):
    today = today or datetime.date.today().isoformat()
    pi, ci = index(prev), index(cur)
    seen, rows = set(), []
    new, moved_in, moved_out, same = [], [], [], []
    for b in cur["blips"]:
        p = pi.get(key(b)) or pi.get("n:" + norm(b["name"]))
        if not p: new.append(b); continue
        d = RANK[b["ring"]] - RANK[p["ring"]]
        rec = {"name": b["name"], "from": LABEL[p["ring"]], "to": LABEL[b["ring"]], "reason": b.get("ring_reason", "")}
        (moved_in if d < 0 else moved_out if d > 0 else same).append(rec if d else {"name": b["name"], "ring": LABEL[b["ring"]]})
    cur_names = {norm(b["name"]) for b in cur["blips"]}; cur_ids = {b.get("tool_id") for b in cur["blips"] if b.get("tool_id")}
    reasons = {norm(d.get("name")): d.get("reason", "") for d in cur.get("dropped", [])}
    dropped = [{"name": b["name"], "was": LABEL[b["ring"]], "reason": reasons.get(norm(b["name"]), "")} for b in prev["blips"]
               if norm(b["name"]) not in cur_names and b.get("tool_id") not in cur_ids]
    ring_counts = lambda s: {r: sum(1 for b in s["blips"] if LABEL[b["ring"]].lower() == r) for r in ("adopt", "trial", "assess", "caution")}
    doms = lambda s: {}
    for s in (prev, cur):
        pass
    def per_domain(s):
        out = {}
        for b in s["blips"]: out[b.get("domain", "")] = out.get(b.get("domain", ""), 0) + 1
        return out
    pd_, cd_ = per_domain(prev), per_domain(cur)
    overdue = [b["name"] for b in cur["blips"] if b.get("next_review") and b["next_review"] < today]
    acts = cur.get("actions", [])
    return {"previous": prev["meta"].get("edition"), "current": cur["meta"].get("edition"),
            "new": [{"name": b["name"], "ring": LABEL[b["ring"]]} for b in new], "moved_in": moved_in, "moved_out": moved_out, "unchanged": len(same), "dropped": dropped,
            "metrics": {"tools_before": len(prev["blips"]), "tools_now": len(cur["blips"]), "by_ring_before": ring_counts(prev), "by_ring_now": ring_counts(cur),
                        "tools_per_domain": {d: {"before": pd_.get(d, 0), "now": cd_.get(d, 0)} for d in sorted(set(pd_) | set(cd_)) if d},
                        "overdue_reviews": overdue, "actions_done": sum(1 for a in acts if (a.get("status") or "").lower() == "done"),
                        "actions_open": sum(1 for a in acts if (a.get("status") or "").lower() != "done")}}


def history(snapshots, cur, b):
    """[(edition_id, ring label)] for one tool across kept snapshots plus the current state."""
    k, n = key(b), norm(b["name"]); out = []
    for eid, s in sorted(snapshots.items()):
        m = next((x for x in s["blips"] if (k == key(x) and b.get("tool_id")) or norm(x["name"]) == n), None)
        if m: out.append((eid, LABEL[m["ring"]]))
    cid = cur["meta"].get("edition")
    if cid and (not out or out[-1][0] != cid): out.append((cid, LABEL[b["ring"]]))
    return out


def to_markdown(c):
    L = [f"# What changed since {c['previous']}", "", f"{len(c['new'])} new, {len(c['moved_in'])} moved toward Adopt, {len(c['moved_out'])} moved toward Caution, {len(c['dropped'])} dropped, {c['unchanged']} unchanged.", ""]
    for title, items, fmt in (("New", c["new"], lambda x: f"{x['name']} (now {x['ring']})"), ("Moved toward Adopt", c["moved_in"], lambda x: f"{x['name']}: {x['from']} to {x['to']}" + (f". {x['reason']}" if x["reason"] else "")),
                              ("Moved toward Caution", c["moved_out"], lambda x: f"{x['name']}: {x['from']} to {x['to']}" + (f". {x['reason']}" if x["reason"] else "")), ("Dropped", c["dropped"], lambda x: f"{x['name']} (was {x['was']})" + (f". {x['reason']}" if x["reason"] else ""))):
        if items: L += [f"## {title}"] + [f"- {fmt(x)}" for x in items] + [""]
    m = c["metrics"]
    L += ["## Numbers", f"- Tools: {m['tools_before']} before, {m['tools_now']} now", f"- Actions: {m['actions_done']} done, {m['actions_open']} open", f"- Reviews overdue: {len(m['overdue_reviews'])}"]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("state", nargs="?", default="radar-state.json"); ap.add_argument("--previous"); ap.add_argument("--out")
    a = ap.parse_args(); cur = json.loads(pathlib.Path(a.state).read_text(encoding="utf-8")); cid = cur["meta"].get("edition") or edition_id()
    cur["meta"]["edition"] = cid
    if a.previous: pp = pathlib.Path(a.previous); pid = pp.stem
    else: pid, pp = find_previous(a.state, cid)
    if not pp: sys.exit("No earlier edition found. This looks like your first edition, so there is nothing to compare yet.")
    prev = json.loads(pp.read_text(encoding="utf-8")); prev["meta"].setdefault("edition", pid)
    c = compare(prev, cur); out = pathlib.Path(a.out or pathlib.Path(a.state).resolve().parent / "radar-output"); out.mkdir(parents=True, exist_ok=True)
    (out / "changes.json").write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"); (out / "changes.md").write_text(to_markdown(c), encoding="utf-8")
    print(to_markdown(c))


if __name__ == "__main__":
    main()
