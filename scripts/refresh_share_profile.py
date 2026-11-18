#!/usr/bin/env python3
"""Pre-fill a new round's share profile from your latest radar and your previous profile (stdlib only).

  python scripts/refresh_share_profile.py radar-state.json --kit round-kit.json --previous-profile old-share-profile.json
         [--previous-contribution old-contribution.json] [--out share-profile.json]

Carries over: organisation, attribution, profile, calibration, tool mapping, scale, caution tags, exclusions.
Moves "real use" forward by the time that passed (a tool you had used for under 6 months, 7 months ago, is now 6 to 12 months).
Leaves consent OFF: you confirm again every round. Prints what it carried over and what still needs an answer.
"""
import argparse, datetime, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import registry as R
import validate_contribution as V

MIN_MONTHS = {"lt-6m": 0, "6-12m": 6, "1-3y": 12, "gt-3y": 36}
ORDER = V.VOCAB["experience"]


def bucket(m): return "lt-6m" if m < 6 else "6-12m" if m < 12 else "1-3y" if m < 36 else "gt-3y"


def advance(b, months):
    """Lower bound of the old bucket plus elapsed months: a safe minimum, so the new bucket is never too high."""
    return b if b in ("none", "gt-3y") or b not in MIN_MONTHS else bucket(MIN_MONTHS[b] + max(0, months))


def months_between(a, b):
    a, b = datetime.date.fromisoformat(a), datetime.date.fromisoformat(b)
    return (b.year - a.year) * 12 + (b.month - a.month) - (1 if b.day < a.day else 0)


def refresh(state, kit, prev, prev_contrib, registry, today=None):
    today = today or datetime.date.today().isoformat()
    as_of = prev.get("as_of") or (prev_contrib or {}).get("generated")
    elapsed = months_between(as_of, today) if as_of else 0
    kd = set(kit["domains"]); pb = prev.get("blips", {}); ptm = prev.get("tool_map", {})
    pc = {b["tool_id"]: b for b in (prev_contrib or {}).get("blips", [])}
    out = {"schema": "byor-share-profile/1", "round_id": kit["round_id"], "as_of": today, "org_name": prev.get("org_name", ""),
           "attribution": prev.get("attribution", kit["default_attribution"]), "profile": prev.get("profile", {}), "calibration": prev.get("calibration", {}),
           "exclude_domains": prev.get("exclude_domains", []), "tool_map": {}, "blips": {},
           "consent": {k: False for k in ("acknowledged_withdrawal", "acknowledged_attribution", "acknowledged_convener_sees_name", "reviewed_preview")}}
    s = {"carried": 0, "advanced": [], "needs_details": [], "ring_changed": [], "needs_tags": [], "needs_real_use": [], "dropped": [], "warnings": []}
    if not as_of: s["warnings"].append("No date on the previous profile, so real-use time was not moved forward. Ask about it.")
    seen = set()
    for b in state["blips"]:
        if b.get("domain") not in kd or state.get("domains", {}).get(b["domain"], {}).get("status") != "done": continue
        name = b["name"]; seen.add(name)
        tid = b.get("tool_id") or ptm.get(name) or registry.resolve(name)[0]
        if tid: out["tool_map"][name] = "custom" if str(tid).startswith("x-") else tid
        p = pb.get(name)
        if not p:
            s["needs_details"].append(name); continue
        new = {k: p[k] for k in ("include", "scale", "caution_tags", "rationale") if k in p}; new.setdefault("include", True)
        old_e = p.get("experience"); new["experience"] = advance(old_e, elapsed) if old_e else None
        if old_e and new["experience"] != old_e: s["advanced"].append(f"{name}: {old_e} to {new['experience']}")
        ring = {"hold": "caution"}.get(b["ring"], b["ring"]); before = pc.get(tid or "", {}).get("ring")
        if before and before != ring: s["ring_changed"].append(f"{name}: {before} to {ring}")
        if ring == "caution" and not new.get("caution_tags"): s["needs_tags"].append(name)
        if ring in ("adopt", "trial") and new.get("experience") in (None, "none"): s["needs_real_use"].append(name)
        if new["experience"] is None: s["needs_details"].append(name); continue
        out["blips"][name] = new; s["carried"] += 1
    s["dropped"] = sorted(n for n in pb if n not in seen)
    return out, s


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("state"); ap.add_argument("--kit", required=True); ap.add_argument("--previous-profile", required=True)
    ap.add_argument("--previous-contribution"); ap.add_argument("--registry"); ap.add_argument("--out", default="share-profile.json"); a = ap.parse_args()
    ld = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    kit = ld(a.kit); E, _ = V.validate_kit(kit)
    if E: sys.exit("Round kit invalid:\n  " + "\n  ".join(E))
    out, s = refresh(ld(a.state), kit, ld(a.previous_profile), ld(a.previous_contribution) if a.previous_contribution else None, R.load(a.registry))
    pathlib.Path(a.out).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(s, indent=1)); print(f"Wrote {a.out}. Consent is OFF; confirm it again before export.", file=sys.stderr)


if __name__ == "__main__":
    main()
