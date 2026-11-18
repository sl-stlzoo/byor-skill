#!/usr/bin/env python3
"""Validate a BYOR radar file (CSV or JSON) and optionally its radar-state.json.   (stdlib only)

Usage:
  python scripts/validate_radar.py radar-output/radar.csv
  python scripts/validate_radar.py radar-output/radar.json --state radar-state.json
  python scripts/validate_radar.py radar.csv --hosted      # enforce BYOR default names (radar.thoughtworks.com)
  python scripts/validate_radar.py radar.csv --json        # machine-readable report
Exit code: 0 = no errors (warnings allowed), 1 = errors found.
"""
import argparse, csv, json, re, sys, collections

RINGS_OK = {"adopt", "trial", "assess", "hold", "caution"}
Q_DEFAULT = {"techniques", "platforms", "tools", "languages & frameworks"}
ALLOWED_TAGS = {"p", "a", "b", "i", "strong", "em", "ul", "ol", "li", "br", "code", "span"}
STATUS_OK = {"new", "moved in", "moved out", "no change", ""}
REQUIRED = ["name", "ring", "quadrant", "isnew", "description"]


def load_rows(path):
    if path.lower().endswith(".json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise SystemExit("JSON root must be an array of objects")
        return data
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--state")
    ap.add_argument("--hosted", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-total", type=int, default=120)
    ap.add_argument("--max-per-quadrant", type=int, default=40)
    ap.add_argument("--min-words", type=int, default=15)
    ap.add_argument("--max-words", type=int, default=140)
    ap.add_argument("--max-name", type=int, default=40)
    a = ap.parse_args()

    errors, warns = [], []
    E = lambda m: errors.append(m)
    W = lambda m: warns.append(m)

    rows = load_rows(a.file)
    if not rows:
        E("No rows found.")
    else:
        cols = {k.strip().lower() for k in rows[0].keys()}
        for c in REQUIRED:
            if c not in cols:
                E(f"Missing required column: {c}")
    norm = [{(k or "").strip().lower(): (str(v) if v is not None else "").strip() for k, v in r.items()} for r in rows]

    names = collections.Counter()
    quads, rings = collections.Counter(), collections.Counter()
    for i, r in enumerate(norm, start=2):
        n = r.get("name", "")
        loc = f"row {i} ({n or 'no name'})"
        if not n: E(f"{loc}: empty name")
        names[n.lower()] += 1
        if len(n) > a.max_name: W(f"{loc}: name is {len(n)} chars; long names crowd the radar")
        ring = r.get("ring", "").lower()
        if ring not in RINGS_OK and not a.state:
            W(f"{loc}: ring '{r.get('ring')}' is not a BYOR default (adopt/trial/assess/hold|caution); OK only if self-hosting with RINGS")
        rings[ring] += 1
        q = r.get("quadrant", "").lower()
        quads[q] += 1
        if a.hosted and q not in Q_DEFAULT:
            E(f"{loc}: quadrant '{r.get('quadrant')}' not a BYOR default name; use --compat export or self-host")
        if a.hosted and ring not in RINGS_OK:
            E(f"{loc}: ring '{r.get('ring')}' not accepted by the hosted site")
        if r.get("isnew", "").upper() not in {"TRUE", "FALSE"}:
            E(f"{loc}: isNew must be TRUE or FALSE (got '{r.get('isnew')}')")
        if r.get("status", "").lower() not in STATUS_OK:
            E(f"{loc}: status must be New / Moved In / Moved Out / No Change (got '{r.get('status')}')")
        d = r.get("description", "")
        words = len(re.sub(r"<[^>]+>", " ", d).split())
        if not d: W(f"{loc}: empty description")
        elif words < a.min_words: W(f"{loc}: description only {words} words")
        elif words > a.max_words: W(f"{loc}: description {words} words (> {a.max_words}); consider trimming")
        for t in re.findall(r"</?\s*([a-zA-Z0-9]+)", d):
            if t.lower() in {"script", "iframe", "style", "object", "embed"}:
                E(f"{loc}: forbidden HTML tag <{t}>")
            elif t.lower() not in ALLOWED_TAGS:
                W(f"{loc}: HTML tag <{t}> may be stripped by BYOR sanitizer")
        for col in ("name", "description"):
            if r.get(col, "")[:1] in ("=", "+", "-", "@"): W(f"{loc}: {col} starts with a formula character; export neutralises it for CSV, but check the text")
        if re.search(r"(password|secret|api[_ -]?key|token)\s*[:=]", d, re.I):
            E(f"{loc}: description looks like it contains a credential")

    for n, c in names.items():
        if n and c > 1: E(f"Duplicate blip name '{n}' appears {c} times (BYOR needs unique names)")
    if len([q for q in quads if q]) > 4: E(f"{len(quads)} distinct quadrants; BYOR draws exactly 4")
    if len([r for r in rings if r]) > 4: E(f"{len(rings)} distinct rings; BYOR supports at most 4")
    total = len(norm)
    if total > a.max_total: W(f"{total} blips total (> {a.max_total}); radar may be hard to read")
    for q, c in quads.items():
        if c > a.max_per_quadrant: W(f"Quadrant '{q}' has {c} blips (> {a.max_per_quadrant})")
    if total:
        for r_, c in rings.items():
            if c / total > 0.6 and total >= 10: W(f"{c}/{total} blips are in ring '{r_}'; check calibration")
        if "adopt" not in rings and total >= 10: W("No blips in Adopt; is the rubric too strict?")
        if not any(r_ in rings for r_ in ("hold", "caution")) and total >= 15:
            W("Nothing in Hold/Caution; radars usually record what to stop or avoid too")
    if len([q for q in quads if q]) < 4 and total >= 8:
        W(f"Only {len([q for q in quads if q])} quadrant(s) populated")

    if a.state:
        with open(a.state, encoding="utf-8") as f:
            st = json.load(f)
        qn = {q["name"].lower() for q in st.get("quadrants", [])}
        rn = {r["name"].lower() for r in st.get("rings", [])} | {"caution", "hold"}
        for i, r in enumerate(norm, start=2):
            if not a.hosted and r.get("quadrant", "").lower() not in qn and r.get("quadrant", "").lower() not in Q_DEFAULT:
                E(f"row {i}: quadrant '{r.get('quadrant')}' not defined in state")
            if r.get("ring", "").lower() not in rn:
                E(f"row {i}: ring '{r.get('ring')}' not defined in state")
        done = {k for k, v in st.get("domains", {}).items() if v.get("status") == "done"}
        pend = [k for k, v in st.get("domains", {}).items() if v.get("status") in ("pending", "in_progress")]
        if pend: W(f"{len(pend)} domain(s) not finished: {', '.join(sorted(pend))}")

    report = {"file": a.file, "blips": total, "errors": errors, "warnings": warns,
              "by_ring": dict(rings), "by_quadrant": dict(quads)}
    if a.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Checked {total} blips in {a.file}")
        print(f"  by ring:     {dict(rings)}")
        print(f"  by quadrant: {dict(quads)}")
        for m in errors: print(f"  ERROR   {m}")
        for m in warns: print(f"  WARNING {m}")
        print("RESULT:", "FAIL" if errors else ("PASS with warnings" if warns else "PASS"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
