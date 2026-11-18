#!/usr/bin/env python3
"""Sanity-check config/*.yaml (needs PyYAML: pip install pyyaml). Use after editing config or adding config.local overrides."""
import sys, yaml, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
dom = yaml.safe_load((root / "config/domains.yaml").read_text())["domains"]
qs = yaml.safe_load((root / "config/quadrants.yaml").read_text())["schemes"]
errs = []
ids = [d["id"] for d in dom]
if len(ids) != len(set(ids)): errs.append("duplicate domain ids")
scheme = yaml.safe_load((root / "config/settings.yaml").read_text())["quadrant_scheme"]
qids = {q["id"] for q in qs.get(scheme, {}).get("quadrants", [])}
for d in dom:
    for k in ("id", "name", "quadrant", "scope", "probes", "seeds", "lens"):
        if k not in d: errs.append(f"{d.get('id','?')}: missing {k}")
    if qids and d.get("quadrant") not in qids: errs.append(f"{d['id']}: unknown quadrant {d.get('quadrant')}")
if scheme != "custom" and len(qids) != 4: errs.append(f"scheme {scheme} must have 4 quadrants")
print(f"{len(dom)} domains, scheme '{scheme}', quadrants {sorted(qids)}")
print("\n".join("ERROR " + e for e in errs) or "Config OK")
sys.exit(1 if errs else 0)
