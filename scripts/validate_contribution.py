#!/usr/bin/env python3
"""STRICT validator for consortium contribution files and round kits (stdlib only). Run by members before sending and by the
convener on intake. Unknown keys, wrong types, free text outside the allowed fields, markup, URLs and bad hashes are errors.

  python scripts/validate_contribution.py contribution.json --kit round-kit.json [--registry config/tools.json]
  python scripts/validate_contribution.py --kit-only round-kit.json
Exit 0 = valid (warnings allowed), 1 = invalid.
"""
import argparse, datetime, hashlib, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import registry as reg_mod

ROOT = pathlib.Path(__file__).resolve().parent.parent
VOCAB = json.loads((ROOT / "config" / "consortium-vocab.json").read_text(encoding="utf-8"))
SCHEMA = "byor-consortium-contribution/1"; KIT_SCHEMA = "byor-consortium-round-kit/1"
NAME_RE = re.compile(r"^[\w .,&'()/-]{1,%d}$" % VOCAB["limits"]["org_name_chars"])
ID_RE = re.compile(r"^(x-)?[a-z0-9]+(-[a-z0-9]+)*$")
BAD_TEXT = re.compile(r"[<>`\x00-\x08\x0b-\x1f]|https?:|www\.|@|\{\{|\bjavascript:", re.I)


def canon(o): return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
def sha(o): return hashlib.sha256(canon(o).encode("utf-8")).hexdigest()
def body_hash(c): return sha({k: v for k, v in c.items() if k != "integrity"})
def kit_hash(kit): return sha(kit)


def keys(o, required, optional, path, E):
    if not isinstance(o, dict): E.append(f"{path}: must be an object"); return False
    for k in required:
        if k not in o: E.append(f"{path}: missing '{k}'")
    for k in o:
        if k not in required and k not in optional: E.append(f"{path}: unknown key '{k}'")
    return True


def validate_kit(kit):
    E, W = [], []
    if not keys(kit, ["schema", "round_id", "title", "convener", "registry_version", "rubric_version", "domains", "min_cohort", "deadline", "default_attribution", "allow_custom_tools"], ["notes", "previous_round_id", "sequence"], "kit", E): return E, W
    if kit["schema"] != KIT_SCHEMA: E.append(f"kit.schema must be {KIT_SCHEMA}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,40}", str(kit["round_id"])): E.append("kit.round_id: lowercase letters, digits, hyphens")
    for k in ("title", "convener"):
        if not isinstance(kit[k], str) or not NAME_RE.match(kit[k]) or BAD_TEXT.search(kit[k]): E.append(f"kit.{k}: invalid text")
    if "previous_round_id" in kit and not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,40}", str(kit["previous_round_id"])): E.append("kit.previous_round_id: lowercase letters, digits, hyphens")
    if "sequence" in kit and not (isinstance(kit["sequence"], int) and kit["sequence"] >= 1): E.append("kit.sequence must be an integer >= 1")
    if kit.get("notes") and (len(kit["notes"]) > VOCAB["limits"]["kit_notes_chars"] or BAD_TEXT.search(kit["notes"])): E.append("kit.notes: too long or contains markup/URLs")
    if kit["rubric_version"] != VOCAB["rubric_version"]: W.append(f"kit rubric_version {kit['rubric_version']} differs from this repo's vocab {VOCAB['rubric_version']}")
    if not (isinstance(kit["domains"], list) and kit["domains"] and all(isinstance(d, str) and re.fullmatch(r"[a-z0-9-]+", d) for d in kit["domains"])): E.append("kit.domains: list of domain ids")
    if not (isinstance(kit["min_cohort"], int) and kit["min_cohort"] >= 3): E.append("kit.min_cohort must be an integer >= 3 (privacy floor)")
    try: datetime.date.fromisoformat(kit["deadline"])
    except Exception: E.append("kit.deadline must be YYYY-MM-DD")
    if kit["default_attribution"] not in ("named", "anonymous"): E.append("kit.default_attribution: named|anonymous")
    if not isinstance(kit["allow_custom_tools"], bool): E.append("kit.allow_custom_tools must be boolean")
    return E, W


def validate(c, kit, registry):
    E, W = [], []
    if not keys(c, ["schema", "round", "contributor", "calibration", "domains_covered", "domains_skipped", "blips", "consent", "generated", "integrity"], [], "contribution", E): return E, W
    if c["schema"] != SCHEMA: E.append(f"schema must be {SCHEMA}")
    r = c["round"]
    if keys(r, ["id", "registry_version", "rubric_version", "kit_sha256"], [], "round", E):
        if r["id"] != kit["round_id"]: E.append("round.id does not match the kit")
        if r["registry_version"] != kit["registry_version"]: E.append("round.registry_version does not match the kit")
        if r["registry_version"] != registry.version: E.append(f"registry on this machine is {registry.version}, round uses {r['registry_version']}: update config/tools.json")
        if r["rubric_version"] != kit["rubric_version"]: E.append("round.rubric_version does not match the kit")
        if r["kit_sha256"] != kit_hash(kit): E.append("round.kit_sha256 does not match the kit (different or edited kit)")
    ct = c["contributor"]
    if keys(ct, ["org_name", "attribution", "profile"], [], "contributor", E):
        if not isinstance(ct["org_name"], str) or not NAME_RE.match(ct["org_name"]) or BAD_TEXT.search(ct["org_name"]): E.append("contributor.org_name: invalid characters or length")
        if ct["attribution"] not in ("named", "anonymous"): E.append("contributor.attribution: named|anonymous")
        p = ct["profile"]
        if keys(p, ["sector", "size_band", "region"], [], "profile", E):
            for k, v in (("sector", VOCAB["sectors"]), ("size_band", VOCAB["size_bands"]), ("region", VOCAB["regions"])):
                if p[k] not in v: E.append(f"profile.{k}: must be one of {v}")
    cal = c["calibration"]
    if keys(cal, list(VOCAB["calibration"]), [], "calibration", E):
        for k, spec in VOCAB["calibration"].items():
            if spec == "boolean":
                if not isinstance(cal[k], bool): E.append(f"calibration.{k}: boolean")
            elif cal[k] not in spec: E.append(f"calibration.{k}: one of {spec}")
    kd = set(kit["domains"])
    for k in ("domains_covered", "domains_skipped"):
        if not (isinstance(c[k], list) and all(isinstance(d, str) for d in c[k])): E.append(f"{k}: list of domain ids"); c[k] = []
        elif any(d not in kd for d in c[k]): E.append(f"{k}: contains domains not in the kit")
    if set(c["domains_covered"]) & set(c["domains_skipped"]): E.append("a domain cannot be both covered and skipped")
    if not c["domains_covered"]: E.append("domains_covered is empty")
    if sorted(set(c["domains_covered"]) | set(c["domains_skipped"])) != sorted(kd): W.append("covered + skipped does not list every kit domain (treated as skipped)")
    bl = c["blips"]
    if not (isinstance(bl, list) and 1 <= len(bl) <= VOCAB["limits"]["max_blips"]): E.append(f"blips: list of 1 to {VOCAB['limits']['max_blips']}")
    else:
        seen, e_months = set(), {"none": 0, "lt-6m": 1, "6-12m": 2, "1-3y": 3, "gt-3y": 4}
        for i, b in enumerate(bl):
            loc = f"blips[{i}]"
            if not keys(b, ["tool_id", "domain", "ring", "experience", "scale"], ["caution_tags", "rationale"], loc, E): continue
            tid = b["tool_id"]
            if not (isinstance(tid, str) and ID_RE.match(tid)): E.append(f"{loc}.tool_id: invalid"); continue
            if tid in seen: E.append(f"{loc}: duplicate tool_id {tid}")
            seen.add(tid)
            if tid.startswith("x-"):
                if not kit["allow_custom_tools"]: E.append(f"{loc}: custom tool {tid} not allowed in this round")
            elif tid not in registry.tools: E.append(f"{loc}: tool_id {tid} is not in the registry")
            if b["domain"] not in c["domains_covered"]: E.append(f"{loc}: domain {b['domain']} not in domains_covered")
            if b["ring"] not in VOCAB["rings"]: E.append(f"{loc}.ring invalid")
            if b["experience"] not in VOCAB["experience"]: E.append(f"{loc}.experience invalid")
            if b["scale"] not in VOCAB["scale"]: E.append(f"{loc}.scale invalid")
            tags = b.get("caution_tags")
            if tags is not None:
                if b["ring"] != "caution": E.append(f"{loc}: caution_tags only allowed on caution blips")
                if not (isinstance(tags, list) and len(tags) <= 4 and all(t in VOCAB["caution_tags"] for t in tags) and len(set(tags)) == len(tags)): E.append(f"{loc}.caution_tags: up to 4 unique values from {VOCAB['caution_tags']}")
            elif b["ring"] == "caution": W.append(f"{loc}: caution without tags; reason will be unknown")
            if "rationale" in b:
                t = b["rationale"]
                if ct.get("attribution") != "named": E.append(f"{loc}: rationale only allowed when attribution is named")
                if not isinstance(t, str) or len(t) > VOCAB["limits"]["rationale_chars"] or BAD_TEXT.search(t): E.append(f"{loc}.rationale: too long or contains markup/URLs/@")
            if b["ring"] in ("adopt", "trial") and b.get("experience") == "none": W.append(f"{loc}: {b['ring']} with no real use is inconsistent; aggregator will treat it as assess")
            if b["ring"] == "adopt" and cal.get("adopt_min_experience") in e_months and e_months.get(b.get("experience"), 0) < e_months[cal["adopt_min_experience"]]: W.append(f"{loc}: adopt below the contributor's own stated minimum experience")
    cs = c["consent"]
    if keys(cs, ["acknowledged_withdrawal", "acknowledged_attribution", "acknowledged_convener_sees_name", "reviewed_preview"], [], "consent", E):
        for k in cs:
            if cs[k] is not True: E.append(f"consent.{k} must be true")
    try: datetime.date.fromisoformat(c["generated"])
    except Exception: E.append("generated must be YYYY-MM-DD")
    ig = c["integrity"]
    if keys(ig, ["sha256"], [], "integrity", E) and ig["sha256"] != body_hash(c): E.append("integrity.sha256 mismatch (file edited after export, or corrupted)")
    return E, W


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("file", nargs="?"); ap.add_argument("--kit"); ap.add_argument("--kit-only"); ap.add_argument("--registry")
    a = ap.parse_args()
    def jl(p):
        try: return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
        except Exception as e: sys.exit(f"Cannot read {p}: {e}")
    if a.kit_only:
        E, W = validate_kit(jl(a.kit_only))
    else:
        if not (a.file and a.kit): sys.exit(__doc__)
        kit = jl(a.kit); E, W = validate_kit(kit)
        if not E: E2, W2 = validate(jl(a.file), kit, reg_mod.load(a.registry)); E += E2; W += W2
    for m in E: print("ERROR  ", m)
    for m in W: print("WARNING", m)
    print("RESULT:", "INVALID" if E else ("VALID with warnings" if W else "VALID")); return 1 if E else 0


if __name__ == "__main__":
    sys.exit(main())
