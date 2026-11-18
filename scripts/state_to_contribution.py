#!/usr/bin/env python3
"""Build a share-safe consortium contribution from radar-state.json + a round kit + the member's share profile.  (stdlib only)

  python scripts/state_to_contribution.py radar-state.json --kit round-kit.json --profile share-profile.json [--preview] [--out FILE]

ONLY these things leave your radar: org name (always, so the convener can run the roster; hidden from members if anonymous), coarse profile,
calibration answers, tool_id + domain + ring + experience bucket + scale (+ caution tags; + short rationale if named).
NEVER copied: descriptions, owners, dates, notes, decision notes, evidence, themes, actions, contributors, quadrants.
Exit 1 and no file written if anything is unmapped, unconfirmed, or invalid.
"""
import argparse, datetime, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import registry as R
import validate_contribution as V

RING = {"adopt": "adopt", "trial": "trial", "assess": "assess", "hold": "caution", "caution": "caution"}


def build(state, kit, prof, registry):
    problems, blips, covered, included_names = [], [], [], []
    kd = set(kit["domains"])
    for did, d in state.get("domains", {}).items():
        if did in kd and d.get("status") == "done" and did not in prof.get("exclude_domains", []): covered.append(did)
    skipped = sorted(kd - set(covered))
    tmap = prof.get("tool_map", {}); per = prof.get("blips", {})
    for b in state["blips"]:
        name = b["name"]; opts = per.get(name, {})
        if b.get("domain") not in covered: continue
        if opts.get("include") is False: continue
        if name not in per: problems.append(f"'{name}': no share settings (experience/scale) in the profile"); continue
        tid = tmap.get(name) or registry.resolve(name)[0]
        if tid == "custom": tid = "x-" + R.slug(name)
        if not tid: problems.append(f"'{name}': no tool_id (confirm a registry match, mark it 'custom', or set include=false)"); continue
        item = {"tool_id": tid, "domain": b["domain"], "ring": RING.get(b["ring"], b["ring"]), "experience": opts.get("experience"), "scale": opts.get("scale")}
        if RING.get(b["ring"]) == "caution" and opts.get("caution_tags"): item["caution_tags"] = opts["caution_tags"]
        if opts.get("rationale") and prof.get("attribution") == "named": item["rationale"] = opts["rationale"]
        blips.append(item); included_names.append(name)
    c = {"schema": V.SCHEMA,
         "round": {"id": kit["round_id"], "registry_version": kit["registry_version"], "rubric_version": kit["rubric_version"], "kit_sha256": V.kit_hash(kit)},
         "contributor": {"org_name": prof.get("org_name", ""), "attribution": prof.get("attribution", kit["default_attribution"]), "profile": prof.get("profile", {})},
         "calibration": prof.get("calibration", {}), "domains_covered": sorted(covered), "domains_skipped": skipped, "blips": blips,
         "consent": prof.get("consent", {}), "generated": datetime.date.today().isoformat()}
    c["integrity"] = {"sha256": V.body_hash(c)}
    return c, problems


def preview(c):
    ct = c["contributor"]
    lines = [f"ROUND: {c['round']['id']}", f"WHO SEES YOUR NAME: {'every member and the convener' if ct['attribution'] == 'named' else 'the convener only (members see an anonymous contributor)'}",
             f"ORGANISATION: {ct['org_name']}  |  {ct['profile'].get('sector')}, {ct['profile'].get('size_band')} staff, {ct['profile'].get('region')}",
             f"CALIBRATION: {json.dumps(c['calibration'])}", f"DOMAINS COVERED ({len(c['domains_covered'])}): {', '.join(c['domains_covered'])}", f"DOMAINS SKIPPED: {', '.join(c['domains_skipped']) or 'none'}", "", f"{'TOOL':34} {'RING':8} {'EXPERIENCE':11} {'SCALE':18} EXTRA"]
    for b in c["blips"]:
        extra = ",".join(b.get("caution_tags", [])) + (f' "{b["rationale"]}"' if "rationale" in b else "")
        lines.append(f"{b['tool_id'][:34]:34} {b['ring']:8} {b['experience']:11} {b['scale']:18} {extra}")
    lines += ["", "NOT SHARED: descriptions, owners, dates, notes, themes, actions, contributor names, quadrants, anything else in your radar."]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("state"); ap.add_argument("--kit", required=True); ap.add_argument("--profile", required=True)
    ap.add_argument("--registry"); ap.add_argument("--out"); ap.add_argument("--preview", action="store_true"); ap.add_argument("--previous-contribution")
    a = ap.parse_args()
    ld = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    state, kit, prof = ld(a.state), ld(a.kit), ld(a.profile); registry = R.load(a.registry)
    kE, _ = V.validate_kit(kit)
    if kE: sys.exit("Round kit invalid:\n" + "\n".join(kE))
    if prof.get("round_id") != kit["round_id"]: sys.exit("share profile round_id does not match the kit")
    c, problems = build(state, kit, prof, registry)
    if problems: sys.exit("Cannot build contribution:\n  " + "\n  ".join(problems))
    if a.preview:                                   # preview happens BEFORE consent; validate content as if consent were given
        c["consent"] = {k: True for k in ("acknowledged_withdrawal", "acknowledged_attribution", "acknowledged_convener_sees_name", "reviewed_preview")}
        c["integrity"] = {"sha256": V.body_hash(c)}
    E, W = V.validate(c, kit, registry)
    if a.previous_contribution:
        pc = {b["tool_id"]: b for b in ld(a.previous_contribution).get("blips", [])}; order = V.VOCAB["experience"]
        for b in c["blips"]:
            o = pc.get(b["tool_id"])
            if o and order.index(b["experience"]) < order.index(o["experience"]): W.append(f"{b['tool_id']}: real use went from {o['experience']} to {b['experience']}. Time only moves forward; check this answer.")
    for w in W: print("WARNING", w, file=sys.stderr)
    if E: sys.exit("Contribution invalid:\n  " + "\n  ".join(E))
    if a.preview: print(preview(c)); return
    out = pathlib.Path(a.out or pathlib.Path(a.state).resolve().parent / "radar-output" / f"contribution-{kit['round_id']}.json")
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({len(c['blips'])} blips, sha256 {c['integrity']['sha256'][:12]}...). Send it only via the convener's agreed secure channel.")


if __name__ == "__main__":
    main()
