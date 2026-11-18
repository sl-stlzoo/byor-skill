#!/usr/bin/env python3
"""Post-deploy smoke test. Run on a machine with internet access.   python scripts/verify_deploy.py [OWNER] [REPO] [REF]   (defaults come from project.json)
Checks that the files an LLM client needs are publicly reachable and look right. Exit 1 on any failure."""
import sys, urllib.request, urllib.error, re, json, pathlib
cfg = json.loads((pathlib.Path(__file__).resolve().parent.parent / "project.json").read_text())
owner = sys.argv[1] if len(sys.argv) > 1 else (cfg["owner"] if cfg["owner"] != "OWNER" else sys.exit("No owner configured. Run scripts/set_owner.py first, or pass OWNER."))
repo = sys.argv[2] if len(sys.argv) > 2 else cfg["repo"]; br = sys.argv[3] if len(sys.argv) > 3 else cfg["branch"]
raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{br}/"; pages = f"https://{owner}.github.io/{repo}/"
checks = [(raw + "AGENTS.md", "skills/byor-radar-builder", True), (raw + "BUNDLE.md", "=== FILE: AGENTS.md ===", True), (raw + "BUNDLE-FULL.md", "=== FILE: scripts/build_site.py ===", False),
          (raw + "skills/byor-radar-builder/SKILL.md", "name: byor-radar-builder", True), (raw + "config/domains.yaml", "id: wealth-screening", True),
          (raw + "scripts/build_site.py", "def build(", True), (pages, "Copy this prompt", False), (pages + "AGENTS.md", "AGENTS.md", False)]
bad = 0
for url, needle, must in checks:
    try:
        body = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "verify"}), timeout=20).read().decode("utf-8", "replace")
        ok = needle in body; note = "" if ok else f"missing text: {needle!r}"
        if url.endswith("AGENTS.md") and "OWNER/" in body and "raw.githubusercontent.com/OWNER" in body: ok = False; note = "placeholder OWNER still present; run set_owner.py"
        if "BUNDLE" in url and len(body) < 40_000: ok = False; note = "bundle looks too small"
    except urllib.error.HTTPError as e: ok, note = False, f"HTTP {e.code}" + (" (Pages not enabled yet?)" if "github.io" in url else " (repo private or file not pushed?)")
    except Exception as e: ok, note = False, str(e)
    print(("PASS " if ok else ("FAIL " if must else "WARN ")) + url + (" " + note if note else ""))
    bad += (not ok) and must
print("RESULT:", "READY" if not bad else f"{bad} required check(s) failed")
sys.exit(1 if bad else 0)
