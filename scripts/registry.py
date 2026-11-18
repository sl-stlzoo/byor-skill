#!/usr/bin/env python3
"""Canonical tool registry helper (stdlib only).

  python scripts/registry.py resolve "Office 365" "AWS"        # name -> tool_id (exact, or suggestions)
  python scripts/registry.py match radar-state.json            # every blip: exact id / suggestions / unresolved (JSON)
  python scripts/registry.py annotate radar-state.json [--write]   # add tool_id to blips with an exact match; list the rest
  python scripts/registry.py merge OLD_ID NEW_ID                   # record that OLD is now NEW (ids are never deleted or reused)
  python scripts/registry.py check                             # registry integrity (unique ids, no alias collisions)
  python scripts/registry.py add ID "Name" [--alias A]... [--domain D]... [--licence foss|oss-core|commercial]

Matching NEVER auto-merges on fuzzy similarity: suggestions must be confirmed by the user.
"""
import argparse, difflib, json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "config" / "tools.json"


def norm(s):
    s = (s or "").lower().replace("&", " and ")
    s = re.sub(r"\((foss|oss-core)\)", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def slug(s): return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


class Registry:
    def __init__(self, data):
        self.version = data.get("registry_version", "")
        self.tools = {t["id"]: t for t in data["tools"]}
        self.index = {}
        for t in data["tools"]:
            target = t.get("merged_into") or t["id"]            # a merged tool resolves to the tool it was merged into
            for n in [t["name"]] + t.get("aliases", []):
                self.index.setdefault(norm(n), set()).add(target)

    def resolve(self, name):
        ids = sorted(self.index.get(norm(name), []))
        if len(ids) == 1: return ids[0], "exact", ids
        return None, ("ambiguous" if ids else "none"), ids

    def suggest(self, name, n=3, cutoff=0.78):
        keys = list(self.index)
        out, seen = [], set()
        for k in difflib.get_close_matches(norm(name), keys, n=n * 2, cutoff=cutoff):
            for i in sorted(self.index[k]):
                if i not in seen: seen.add(i); out.append({"id": i, "name": self.tools[i]["name"], "score": round(difflib.SequenceMatcher(None, norm(name), k).ratio(), 2)})
        return out[:n]


def load(path=None):
    return Registry(json.loads(pathlib.Path(path or DEFAULT).read_text(encoding="utf-8")))


def migration_map(data):
    """{old_id: new_id} for tools merged into another tool (used to compare rounds across registry versions)."""
    return {t["id"]: t["merged_into"] for t in data["tools"] if t.get("merged_into")}


def check(data):
    errs, seen, alias_owner = [], set(), {}
    ids = {t["id"] for t in data["tools"]}
    for t in data["tools"]:
        m = t.get("merged_into")
        if m and (m not in ids or m == t["id"] or any(x["id"] == m and x.get("merged_into") for x in data["tools"])): errs.append(f"{t['id']}: merged_into {m!r} must be a different tool that is not itself merged")
        if t.get("merged_into"): continue
    for t in data["tools"]:
        if t.get("merged_into"): continue
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", t["id"]): errs.append(f"bad id {t['id']!r}")
        if t["id"] in seen: errs.append(f"duplicate id {t['id']}")
        seen.add(t["id"])
        for n in [t["name"]] + t.get("aliases", []):
            o = alias_owner.setdefault(norm(n), t["id"])
            if o != t["id"]: errs.append(f"name/alias {n!r} used by both {o} and {t['id']}")
    return errs


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resolve"); r.add_argument("names", nargs="+"); r.add_argument("--registry")
    m = sub.add_parser("match"); m.add_argument("state"); m.add_argument("--registry")
    n = sub.add_parser("annotate"); n.add_argument("state"); n.add_argument("--write", action="store_true"); n.add_argument("--registry")
    g = sub.add_parser("merge"); g.add_argument("old"); g.add_argument("new"); g.add_argument("--registry")
    c = sub.add_parser("check"); c.add_argument("--registry")
    a = sub.add_parser("add"); a.add_argument("id"); a.add_argument("name"); a.add_argument("--alias", action="append", default=[])
    a.add_argument("--domain", action="append", default=[]); a.add_argument("--licence", default="commercial", choices=["foss", "oss-core", "commercial"]); a.add_argument("--registry")
    x = ap.parse_args()
    path = pathlib.Path(x.registry or DEFAULT)
    if x.cmd == "resolve":
        reg = load(path)
        for n in x.names:
            i, st, ids = reg.resolve(n)
            print(json.dumps({"input": n, "tool_id": i, "status": st, "candidates": ids if st == "ambiguous" else reg.suggest(n)}))
    elif x.cmd == "match":
        reg = load(path); state = json.loads(pathlib.Path(x.state).read_text(encoding="utf-8")); res = []
        for b in state["blips"]:
            i, st, ids = reg.resolve(b["name"])
            res.append({"blip": b["name"], "tool_id": i, "status": st, "suggestions": [] if i else (ids if st == "ambiguous" else reg.suggest(b["name"]))})
        print(json.dumps({"registry_version": reg.version, "matches": res}, indent=1))
    elif x.cmd == "annotate":
        reg = load(path); sp = pathlib.Path(x.state); state = json.loads(sp.read_text(encoding="utf-8")); done, ask = 0, []
        for b in state["blips"]:
            if b.get("tool_id"): continue
            i, st, ids = reg.resolve(b["name"])
            if i: b["tool_id"] = i; done += 1
            else: ask.append({"name": b["name"], "status": st, "suggestions": ids if st == "ambiguous" else reg.suggest(b["name"])})
        if x.write and done: sp.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"matched": done, "written": bool(x.write and done), "needs_a_question": ask}, indent=1))
    elif x.cmd == "merge":
        data = json.loads(path.read_text(encoding="utf-8")); by = {t["id"]: t for t in data["tools"]}
        if x.old not in by or x.new not in by: sys.exit("Both ids must exist.")
        by[x.old]["merged_into"] = x.new; errs = check(data)
        if errs: sys.exit("\n".join(errs))
        path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"); print(f"{x.old} now resolves to {x.new}. Bump registry_version and tell members.")
    elif x.cmd == "check":
        errs = check(json.loads(path.read_text(encoding="utf-8")))
        print("\n".join("ERROR " + e for e in errs) or "Registry OK"); sys.exit(1 if errs else 0)
    elif x.cmd == "add":
        data = json.loads(path.read_text(encoding="utf-8"))
        if any(t["id"] == x.id for t in data["tools"]): sys.exit(f"id {x.id} exists; never reuse ids")
        data["tools"].append({"id": slug(x.id), "name": x.name, "aliases": x.alias, "domains": x.domain, "licence": x.licence})
        data["tools"].sort(key=lambda t: t["id"]); errs = check(data)
        if errs: sys.exit("\n".join(errs))
        path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"); print("Added", x.id, "(bump registry_version and tell members)")


if __name__ == "__main__":
    main()
