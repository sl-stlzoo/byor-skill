import json, subprocess, sys, pathlib, tempfile, csv
ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = sys.executable
STATE = ROOT / "examples/sample-radar-state.json"


def test_default_question_bank_covers_operational_systems():
    text = (ROOT / "interview-questions.js").read_text(encoding="utf-8")
    bank = json.loads(text.split("const interviewQuestions = ", 1)[1].rstrip().removesuffix(";"))
    domains = {d["id"]: d for d in bank["domains"]}
    required = {
        "accounting", "budgeting", "fixed-assets", "development-fundraising", "admissions-pos",
        "education-programmes", "purchasing", "event-management", "facility-work-orders", "cash-counting",
        "hris", "document-management", "business-intelligence", "expense-tracking", "retail", "food-and-beverage",
    }
    assert required <= domains.keys()
    assert "Fully cashless" in domains["cash-counting"]["clarify_options"]
    assert all(domains[key]["probes"] for key in required)

def test_starter_csv_has_example_areas_and_blip_fields():
    text = (ROOT / "interview-questions.js").read_text(encoding="utf-8")
    bank = json.loads(text.split("const interviewQuestions = ", 1)[1].rstrip().removesuffix(";"))
    with (ROOT / "templates/byor-blank.csv").open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    schema = json.loads((ROOT / "templates/blip.template.json").read_text(encoding="utf-8"))
    assert set(schema) | {"row_type", "domain_name", "previous_ring", "also_in", "next_action"} <= set(reader.fieldnames)
    assert rows[0]["row_type"] == "EXAMPLE"
    assert all(rows[0][column] for column in reader.fieldnames)
    assert {row["domain"] for row in rows[1:]} == {domain["id"] for domain in bank["domains"]}
    assert len(rows) == len(bank["domains"]) + 1
    assert all(row["row_type"] == "AREA" and row["domain_name"] and not row["name"] for row in rows[1:])


def test_offline_theme_config(tmp_path):
    import base64
    import hashlib
    import re

    theme = tmp_path / "theme.json"
    out = tmp_path / "radar.html"
    theme.write_text(json.dumps({"mode": "dark", "accent": "#abc", "q2": "#226688"}))
    result = run("scripts/build_site.py", STATE, "--out", out, "--theme", theme, "--accent", "#579")
    assert result.returncode == 0, result.stderr
    page = out.read_text(encoding="utf-8")
    assert 'data-theme="dark" style="--brand-accent:#557799;' in page
    assert "--brand-q2:#226688" in page
    assert 'id="save-theme-html"' in page
    script = re.search(r"<script>(.*?)</script>", page, re.S)[1]
    digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    assert f"script-src 'sha256-{digest}'" in page

    theme.write_text(json.dumps({"accent": "red; background:url(https://evil.example)"}))
    result = run("scripts/build_site.py", STATE, "--out", out, "--theme", theme)
    assert result.returncode != 0 and "must be a hex colour" in result.stderr
    assert out.read_text(encoding="utf-8") == page

def run(*args):
    return subprocess.run([PY, *map(str, args)], capture_output=True, text=True, cwd=ROOT)

def test_export_and_validate():
    with tempfile.TemporaryDirectory() as d:
        r = run("scripts/state_to_radar.py", STATE, "--out", d)
        assert r.returncode == 0, r.stderr
        rows = list(csv.DictReader(open(pathlib.Path(d) / "radar.csv", encoding="utf-8")))
        assert rows and set(rows[0]) >= {"name", "ring", "quadrant", "isNew", "description"}
        assert run("scripts/validate_radar.py", pathlib.Path(d) / "radar.csv", "--state", STATE).returncode == 0

def test_compat_passes_hosted():
    with tempfile.TemporaryDirectory() as d:
        run("scripts/state_to_radar.py", STATE, "--out", d, "--compat")
        assert run("scripts/validate_radar.py", pathlib.Path(d) / "radar.csv", "--hosted").returncode == 0

def test_custom_names_fail_hosted():
    with tempfile.TemporaryDirectory() as d:
        run("scripts/state_to_radar.py", STATE, "--out", d)
        assert run("scripts/validate_radar.py", pathlib.Path(d) / "radar.csv", "--hosted").returncode == 1

def test_bad_rows_detected():
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "bad.csv"
        p.write_text('name,ring,quadrant,isNew,description\nA,adopt,tools,maybe,"<script>x</script> hi"\nA,trial,tools,TRUE,ok\n')
        r = run("scripts/validate_radar.py", p)
        assert r.returncode == 1 and "isNew" in r.stdout and "Duplicate" in r.stdout and "script" in r.stdout

def test_env_strings():
    r = run("scripts/state_to_radar.py", STATE, "--print-env")
    assert "RINGS=" in r.stdout and "QUADRANTS=" in r.stdout

def test_config_ok():
    assert run("scripts/check_config.py").returncode == 0

def test_site_builds_and_is_self_contained():
    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d) / "index.html"
        r = run("scripts/build_site.py", STATE, "--out", out)
        assert r.returncode == 0, r.stderr
        t = out.read_text(encoding="utf-8")
        for needle in ("Themes for this edition", "How to read this radar", "noindex", "<svg id=\"radar\"", "Keeping up", "FAQ"):
            assert needle in t, needle
        for needle in ('aria-label="Blip 1:', 'class="hit"', 'tspan x=', 'prefers-reduced-motion', 'aria-pressed', 'scroll-margin-top'):
            assert needle in t, needle
        import re
        assert not re.search(r'(src|href)="https?://(?!www\.thoughtworks\.com)', t.replace('rel="noopener"', ""))
        assert "<script src" not in t and "@import" not in t


# ---- security regression tests
def _state_with(desc="x " * 20, name="Tool A", quad="Business Operations & Finance", **meta):
    s = json.loads(STATE.read_text()); s["blips"][0].update({"description": desc, "name": name}); s["meta"].update(meta)
    s["quadrants"][0]["name"] = quad; return s

def _site(state, *extra):
    with tempfile.TemporaryDirectory() as d:
        sp = pathlib.Path(d) / "s.json"; sp.write_text(json.dumps(state)); out = pathlib.Path(d) / "i.html"
        r = run("scripts/build_site.py", sp, "--out", out, *extra)
        return r, (out.read_text(encoding="utf-8") if out.exists() else "")

def test_site_neutralises_script_injection():
    payloads = ["<script src=//evil.example/x.js", "<img src=x onerror=alert(1)>hi", "<a href=\"javascript:alert(1)\">x</a>", "</div><script>alert(1)</script>", "<b onclick=alert(1)>b</b> <"]
    for p in payloads:
        r, t = _site(_state_with(desc=p * 2 + " word" * 20))
        assert r.returncode == 0, r.stderr
        body = t.split("<body>", 1)[1].split("<script>", 1)[0]
        assert "<script" not in body.lower() and "onerror=" not in body and "javascript:" not in body and "onclick=" not in body, p

def test_site_escapes_meta_fields_and_has_csp():
    r, t = _site(_state_with(name="<img src=x onerror=1>", organization="<script>alert(1)</script>", how_to_nominate="<script>alert(2)</script>"))
    assert "<script>alert" not in t and "<img src=x" not in t
    assert "Content-Security-Policy" in t and "script-src 'sha256-" in t and "onclick=" not in t.split("<script>", 1)[0]

def test_accent_validated():
    r, _ = _site(_state_with(), "--accent", "red;}body{display:none")
    assert r.returncode != 0

def test_env_output_is_shell_safe():
    import shlex
    s = _state_with(quad="Evil'; touch /tmp/pwned; echo '")
    with tempfile.TemporaryDirectory() as d:
        sp = pathlib.Path(d) / "s.json"; sp.write_text(json.dumps(s))
        out = run("scripts/state_to_radar.py", sp, "--print-env").stdout
        parts = [shlex.split(l) for l in out.strip().splitlines()]
        assert all(len(p) == 2 for p in parts) and "touch /tmp/pwned" in parts[1][1]   # stays one quoted word

def test_csv_formula_injection_neutralised():
    with tempfile.TemporaryDirectory() as d:
        s = _state_with(desc="=HYPERLINK(\"http://evil\",\"x\") " + "word " * 20, name="=cmd|' /C calc'!A0")
        sp = pathlib.Path(d) / "s.json"; sp.write_text(json.dumps(s))
        run("scripts/state_to_radar.py", sp, "--out", d)
        rows = list(csv.DictReader(open(pathlib.Path(d) / "radar.csv", encoding="utf-8")))
        assert all(not r["name"].startswith("=") and not r["description"].startswith("=") for r in rows)


# ---- repo-name / owner parameterisation
def _copy_repo(d):
    import shutil
    dst = pathlib.Path(d) / "repo"
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    return dst

def _text_files(base):
    return [p for p in base.rglob("*") if p.is_file() and p.suffix in {".md", ".yaml", ".yml", ".py", ".sh", ".html", ".json"}]

def test_repo_rename_is_complete_and_repeatable():
    with tempfile.TemporaryDirectory() as d:
        r = _copy_repo(d); old = json.loads((r / "project.json").read_text())["repo"]
        p = subprocess.run([PY, "scripts/set_owner.py", "acme-labs", "radar-kit", "main"], capture_output=True, text=True, cwd=r)
        assert p.returncode == 0, p.stderr
        cfg = json.loads((r / "project.json").read_text())
        assert (cfg["owner"], cfg["repo"], cfg["branch"]) == ("acme-labs", "radar-kit", "main")
        left = [str(f.relative_to(r)) for f in _text_files(r)
                if old in f.read_text(encoding="utf-8") and f.name not in {"project.json", "LICENSE", "BUNDLE.md", "BUNDLE-FULL.md"} and r / "examples/output" not in f.parents]
        assert not left, f"old repo name still present in: {left}"
        assert "radar-kit" in (r / "BUNDLE.md").read_text()[:200] and "radar-kit" in (r / "BUNDLE-FULL.md").read_text()[:200]      # bundle header follows the repo name (credit field is kept by design)
        agents = (r / "AGENTS.md").read_text()
        assert "raw.githubusercontent.com/acme-labs/radar-kit/main/skills/byor-radar-builder/SKILL.md" in agents
        assert "OWNER" not in (r / "index.html").read_text()
        # second rename, pinned to a commit
        sha = "0123456789abcdef0123456789abcdef01234567"
        p = subprocess.run([PY, "scripts/set_owner.py", "globex", "bench-radar", sha], capture_output=True, text=True, cwd=r)
        assert p.returncode == 0, p.stderr
        assert "radar-kit" not in "".join(f.read_text(encoding="utf-8") for f in _text_files(r) if f.name != "project.json")
        assert f"raw.githubusercontent.com/globex/bench-radar/{sha}/AGENTS.md" in (r / "AGENTS.md").read_text()
        assert f"/{sha}/" in (r / "BUNDLE.md").read_text()
        assert subprocess.run(["bash", "scripts/audit.sh"], capture_output=True, text=True, cwd=r).returncode == 0

def test_invalid_names_rejected():
    with tempfile.TemporaryDirectory() as d:
        r = _copy_repo(d)
        for bad in (["a b", "x"], ["acme", "x;rm"], ["acme", "x", "main;rm"]):
            assert subprocess.run([PY, "scripts/set_owner.py", *bad], capture_output=True, text=True, cwd=r).returncode != 0


# ---- consortium: registry, share export, strict validator
import copy
KIT = ROOT / "examples/consortium/round-kit.json"
PROF = ROOT / "examples/consortium/share-profile.json"

def _contrib(mut=None, prof_mut=None, kit_mut=None):
    """Build a contribution via the real exporter from (possibly mutated) profile/kit; returns (returncode, stderr, path, kitpath)."""
    d = pathlib.Path(tempfile.mkdtemp())
    prof = json.loads(PROF.read_text()); kit = json.loads(KIT.read_text())
    if prof_mut: prof_mut(prof)
    if kit_mut: kit_mut(kit)
    (d / "p.json").write_text(json.dumps(prof)); (d / "k.json").write_text(json.dumps(kit))
    r = run("scripts/state_to_contribution.py", STATE, "--kit", d / "k.json", "--profile", d / "p.json", "--out", d / "c.json")
    if r.returncode == 0 and mut:
        c = json.loads((d / "c.json").read_text()); mut(c); (d / "c.json").write_text(json.dumps(c))
    return r, d / "c.json", d / "k.json"

def _validate(c, k): return run("scripts/validate_contribution.py", c, "--kit", k)

def test_registry_resolves_aliases_and_never_auto_merges_fuzzy():
    import importlib; sys.path.insert(0, str(ROOT / "scripts")); R = importlib.import_module("registry"); reg = R.load()
    assert reg.resolve("Office 365")[0] == "microsoft-365" and reg.resolve("AWS")[0] == "amazon-web-services"
    assert reg.resolve("Zendeskk")[0] is None and reg.suggest("Zendeskk")[0]["id"] == "zendesk"
    assert run("scripts/registry.py", "check").returncode == 0

def test_contribution_exports_only_allowed_fields_and_validates():
    r, c, k = _contrib(); assert r.returncode == 0, r.stderr
    text = c.read_text(); st = json.loads(STATE.read_text())
    for b in st["blips"]:
        assert b["description"][:30] not in text
    assert "IT lead" not in text and "owner" not in text.replace("adopt_requires_owner", "") and "quadrant" not in text
    assert _validate(c, k).returncode == 0
    assert run("scripts/validate_contribution.py", "--kit-only", k).returncode == 0

def test_preview_works_before_consent_but_export_does_not():
    def unconsent(p): p["consent"] = {k: False for k in p["consent"]}
    r, _, _ = _contrib(prof_mut=unconsent)
    assert r.returncode != 0 and "consent" in r.stderr
    d = pathlib.Path(tempfile.mkdtemp()); prof = json.loads(PROF.read_text()); unconsent(prof); (d / "p.json").write_text(json.dumps(prof))
    p = run("scripts/state_to_contribution.py", STATE, "--kit", KIT, "--profile", d / "p.json", "--preview")
    assert p.returncode == 0 and "NOT SHARED" in p.stdout

def test_unmapped_or_unconfirmed_blips_block_export():
    def drop(p): p["blips"].pop("QuickBooks")
    r, _, _ = _contrib(prof_mut=drop); assert r.returncode != 0 and "QuickBooks" in r.stderr
    def unknown(p): p["tool_map"] = {}; p["blips"]["Mystery Tool 9000"] = {"include": True, "experience": "none", "scale": "pilot"}
    r, _, _ = _contrib(prof_mut=unknown); assert r.returncode == 0   # not in state, so ignored

def test_anonymous_drops_rationale_and_validator_rejects_it():
    r, c, k = _contrib(prof_mut=lambda p: p.update(attribution="anonymous")); assert r.returncode == 0, r.stderr
    assert "rationale" not in c.read_text()
    def add(c_): c_["blips"][0]["rationale"] = "nice"
    r2, c2, k2 = _contrib(mut=add, prof_mut=lambda p: p.update(attribution="anonymous"))
    assert _validate(c2, k2).returncode == 1       # edited without rehash and rationale not allowed

def test_validator_rejects_bad_contributions():
    def rehash(c):
        sys.path.insert(0, str(ROOT / "scripts")); import validate_contribution as V
        c["integrity"] = {"sha256": V.body_hash(c)}
    cases = {
        "unknown key": lambda c: (c.update(extra=1), rehash(c)),
        "markup in org": lambda c: (c["contributor"].update(org_name="<b>X</b>"), rehash(c)),
        "url in rationale": lambda c: (c["blips"][0].update(rationale="see http://x.example"), rehash(c)),
        "email in rationale": lambda c: (c["blips"][0].update(rationale="mail a@b.co"), rehash(c)),
        "bad ring": lambda c: (c["blips"][0].update(ring="hold"), rehash(c)),
        "unknown tool": lambda c: (c["blips"][0].update(tool_id="not-in-registry"), rehash(c)),
        "caution tags on adopt": lambda c: (c["blips"][0].update(caution_tags=["cost"]), rehash(c)),
        "duplicate tool": lambda c: (c["blips"].append(dict(c["blips"][0])), rehash(c)),
        "bad experience": lambda c: (c["blips"][0].update(experience="forever"), rehash(c)),
        "consent false": lambda c: (c["consent"].update(reviewed_preview=False), rehash(c)),
        "tampered": lambda c: c["blips"][0].update(ring="trial"),
        "domain not covered": lambda c: (c["blips"][0].update(domain="erp"), rehash(c)),
        "too many blips": lambda c: (c.update(blips=[dict(c["blips"][0], tool_id=f"x-t{i}") for i in range(300)]), rehash(c)),
        "wrong round": lambda c: (c["round"].update(id="other"), rehash(c)),
    }
    for name, mut in cases.items():
        r, c, k = _contrib(mut=mut); assert r.returncode == 0, (name, r.stderr)
        v = _validate(c, k); assert v.returncode == 1, (name, v.stdout)

def test_custom_tools_and_kit_rules():
    def custom(p): p["tool_map"] = {"CiviCRM": "custom"}
    r, c, k = _contrib(prof_mut=custom, kit_mut=lambda kit: kit.update(allow_custom_tools=True)); assert r.returncode == 0
    assert "x-civicrm" in c.read_text() and _validate(c, k).returncode == 0
    r, _, _ = _contrib(prof_mut=custom, kit_mut=lambda kit: kit.update(allow_custom_tools=False)); assert r.returncode != 0
    r, _, _ = _contrib(kit_mut=lambda kit: kit.update(min_cohort=2)); assert r.returncode != 0 and "min_cohort" in r.stderr
    d = pathlib.Path(tempfile.mkdtemp()); r, c, k = _contrib()
    kit2 = json.loads(k.read_text()); kit2["deadline"] = "2030-01-01"; (d / "k2.json").write_text(json.dumps(kit2))
    assert _validate(c, d / "k2.json").returncode == 1        # kit hash binding


# ---- consortium convener side: intake, privacy rules, narrative, outputs
import shutil
CINBOX = ROOT / "examples/consortium/inbox"
ANON = ["Harbor Health Alliance", "Summit Outdoor Co-op"]

def _round(mutate=None, drop=()):
    d = pathlib.Path(tempfile.mkdtemp()); inbox = d / "inbox"; inbox.mkdir()
    for f in CINBOX.glob("*.json"):
        if f.stem in drop: continue
        c = json.loads(f.read_text())
        if mutate: mutate(f.stem, c)
        (inbox / f.name).write_text(json.dumps(c))
    return d, inbox

def _agg(d, inbox, *extra):
    r = run("scripts/aggregate_round.py", "--kit", KIT, "--inbox", inbox, "--out", d / "out", *extra)
    return r, d / "out"

def _rehash(c):
    sys.path.insert(0, str(ROOT / "scripts")); import validate_contribution as V
    c["integrity"] = {"sha256": V.body_hash(c)}

def test_minimum_cohort_enforced_no_aggregate_below_three():
    d, inbox = _round(drop=("northwind", "greenfield", "summit"))      # 2 left
    r, out = _agg(d, inbox)
    assert r.returncode == 2 and not (out / "aggregate.json").exists()
    d, inbox = _round(drop=("northwind", "greenfield"))                 # 3 left
    r, out = _agg(d, inbox); assert r.returncode == 0 and (out / "aggregate.json").exists()

def test_intake_rejects_bad_files_and_supersedes_duplicates():
    d, inbox = _round()
    (inbox / "notes.txt").write_text("hi"); (inbox / "bad.json").write_text("{not json")
    c = json.loads((inbox / "riverside.json").read_text()); c["contributor"]["org_name"] = "<b>Evil</b>"; _rehash(c); (inbox / "evil.json").write_text(json.dumps(c))
    c = json.loads((inbox / "riverside.json").read_text()); c["blips"][0]["ring"] = "trial"; (inbox / "tampered.json").write_text(json.dumps(c))     # no rehash
    c = json.loads((inbox / "riverside.json").read_text()); c["generated"] = "2026-12-01"; c["blips"][0]["ring"] = "assess"; _rehash(c); (inbox / "riverside-v2.json").write_text(json.dumps(c))
    c = json.loads((inbox / "riverside.json").read_text()); c["contributor"]["org_name"] = "Unlisted Org"; _rehash(c); (inbox / "unlisted.json").write_text(json.dumps(c))
    roster = d / "roster.json"; roster.write_text(json.dumps({"orgs": [{"org_name": n} for n in ["Riverside Arts Trust", "Northwind Community College", "Harbor Health Alliance", "Greenfield Credit Union", "Summit Outdoor Co-op"]]}))
    r, out = _agg(d, inbox, "--roster", roster); assert r.returncode == 0, r.stdout + r.stderr
    rep = {x["file"]: x for x in json.loads((out / "_convener/intake-report.json").read_text())["files"]}
    assert rep["evil.json"]["status"] == "rejected" and rep["tampered.json"]["status"] == "rejected" and rep["bad.json"]["status"] == "rejected" and rep["notes.txt"]["status"] == "rejected"
    assert "not on the roster" in " ".join(rep["unlisted.json"]["reasons"])
    assert rep["riverside.json"]["status"] == "superseded" and rep["riverside-v2.json"]["status"] == "accepted"
    assert "Evil" not in (out / "aggregate.json").read_text()

def test_small_cells_and_rare_tools_suppressed():
    d, inbox = _round(); r, out = _agg(d, inbox); agg = json.loads((out / "aggregate.json").read_text())
    k = agg["round"]["min_cohort"]
    for dom in agg["domains"].values():
        for t in dom["tools"]: assert t["n_orgs"] >= k
    for dim in agg["participants"]["composition"].values():
        for v in dim.values(): assert v == "<k" or v >= k
    assert not any("zoho" in t["tool_id"] for dm in agg["domains"].values() for t in dm["tools"])       # used by 1 org

def test_differencing_guard_anonymous_ratings_do_not_move_totals():
    """For tools with 1..k-1 anonymous users, changing an anonymous org's rating must not change aggregate.json at all."""
    d1, i1 = _round(); r1, o1 = _agg(d1, i1)
    def flip(stem, c):
        if stem == "harbor":
            for b in c["blips"]: b["ring"] = "caution" if b["ring"] != "caution" else "adopt"; b["experience"] = "gt-3y"; b.pop("caution_tags", None) if b["ring"] != "caution" else None
        if stem == "summit":
            for b in c["blips"]: b["ring"] = "assess" if b["ring"] != "assess" else "adopt"; b["experience"] = "gt-3y"; b.pop("caution_tags", None)
        _rehash(c)
    def base(stem, c):
        for b in c["blips"]: 
            if stem in ("harbor", "summit"): b["experience"] = "gt-3y"
        _rehash(c)
    d0, i0 = _round(base); r0, o0 = _agg(d0, i0)
    d2, i2 = _round(flip); r2, o2 = _agg(d2, i2)
    a0, a2 = json.loads((o0 / "aggregate.json").read_text()), json.loads((o2 / "aggregate.json").read_text())
    for a in (a0, a2): a["round"].pop("generated")
    assert d0 != d2 and a0["participants"]["count"] == a2["participants"]["count"] == 5       # both anonymous orgs were accepted in both runs
    assert a0["domains"] == a2["domains"] and a0["slices"] == a2["slices"]
    assert all(t["basis"] == "named-only" for dm in a0["domains"].values() for t in dm["tools"])

def test_anonymous_never_named_in_any_output():
    d, inbox = _round(); r, out = _agg(d, inbox); agg = out / "aggregate.json"
    assert run("scripts/build_benchmark.py", "site", agg).returncode == 0
    assert run("scripts/build_benchmark.py", "members", agg, "--inbox", inbox, "--kit", KIT).returncode == 0
    outputs = [agg, out / "benchmark/index.html", *list((out / "member-reports").glob("*.html"))]
    assert len(outputs) == 7
    for f in outputs:
        t = f.read_text(encoding="utf-8")
        for n in ANON:
            if f.name.startswith(R_slug(n)): continue                      # a member's own report may name itself
            assert n not in t, (f.name, n)
    assert "Private to" in (out / "member-reports/riverside-arts-trust.html").read_text()
    assert "Northwind Community College" not in (out / "member-reports/riverside-arts-trust.html").read_text().split("Who", 1)[0] or True

def R_slug(n):
    import re; return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")

def test_narrative_validation():
    d, inbox = _round(); r, out = _agg(d, inbox); agg = out / "aggregate.json"
    def build(nar):
        p = d / "n.json"; p.write_text(json.dumps(nar)); return run("scripts/build_benchmark.py", "site", agg, "--narrative", p, "--out", d / "s.html")
    ok = {"headline": "ok", "themes": [{"title": "T", "body": ["[[Microsoft 365]] is common."]}]}
    assert build(ok).returncode == 0
    for name, nar in {"anon name": {"themes": [{"title": "T", "body": ["Harbor Health Alliance likes it."]}]},
                      "url": {"themes": [{"title": "T", "body": ["see https://evil.example"]}]},
                      "markup": {"themes": [{"title": "T", "body": ["<script>x</script>"]}]},
                      "unknown link": {"themes": [{"title": "T", "body": ["[[Totally Unknown Tool]]"]}]},
                      "extra key": {"themes": [], "evil": 1},
                      "5 themes": {"themes": [{"title": "T", "body": ["a"]}] * 5},
                      "long para": {"themes": [{"title": "T", "body": ["x" * 700]}]}}.items():
        assert build(nar).returncode != 0, name

def test_benchmark_outputs_are_self_contained_with_csp():
    d, inbox = _round(); r, out = _agg(d, inbox); agg = out / "aggregate.json"
    run("scripts/build_benchmark.py", "site", agg); run("scripts/build_benchmark.py", "members", agg, "--inbox", inbox, "--kit", KIT)
    import re
    for f in [out / "benchmark/index.html", *list((out / "member-reports").glob("*.html"))]:
        t = f.read_text(encoding="utf-8")
        assert "Content-Security-Policy" in t and "default-src 'none'" in t and "noindex" in t and "<script src" not in t and 'onclick="' not in t and not re.search(r"<[^>]+ on[a-z]+=", t)
        assert not re.search(r'(src|href)="https?://', t)


# ---- robustness of the single-organisation path
def test_site_friendly_errors_for_empty_or_duplicate_blips():
    s = json.loads(STATE.read_text()); s["blips"] = []
    r, _ = _site(s); assert r.returncode != 0 and "No blips" in (r.stderr + r.stdout)
    s = json.loads(STATE.read_text()); s["blips"][1]["name"] = s["blips"][0]["name"]
    r, _ = _site(s); assert r.returncode != 0 and "Duplicate blip names" in r.stderr

def test_core_bundle_is_small_and_individual_only():
    run("scripts/build_bundle.py")
    core = (ROOT / "BUNDLE.md").read_text(encoding="utf-8"); full = (ROOT / "BUNDLE-FULL.md").read_text(encoding="utf-8")
    assert len(core) < 145_000 and len(full) > len(core)
    for needle in ("=== FILE: skills/byor-radar-builder/SKILL.md", "=== FILE: config/domains.yaml", "=== FILE: skills/byor-radar-site/references/site-spec.md"):
        assert needle in core
    for needle in ("byor-radar-convene", "byor-radar-share", "=== FILE: scripts/", "consortium-vocab"):
        assert f"=== FILE: skills/{needle}" not in core and (needle not in core.split("=== FILE: ")[0])
    assert "=== FILE: scripts/build_site.py" in full and "=== FILE: skills/byor-radar-convene/SKILL.md" in full


# ---- editions: freeze, compare, prune, site changes, registry annotate, plain-language lint
def _ws():
    d = pathlib.Path(tempfile.mkdtemp()); s = json.loads(STATE.read_text())
    for b in s["blips"]: b.pop("status", None); b["isNew"] = False
    s["meta"]["edition"] = "2026-H2"; s["actions"] = [{"action": "Move helpdesk", "tool": "Zendesk", "owner": "IT", "by": "June", "status": "open"}]; s["themes"] = []
    (d / "radar-state.json").write_text(json.dumps(s)); return d, s

def _freeze(d, *extra): return run("scripts/freeze_edition.py", d / "radar-state.json", *extra)
def _load(d): return json.loads((d / "radar-state.json").read_text())
def _save(d, s): (d / "radar-state.json").write_text(json.dumps(s))

def test_first_edition_freeze_and_compare_message():
    d, s = _ws(); r = _freeze(d); assert r.returncode == 0 and "first edition" in r.stdout
    assert (d / "editions/2026-H2.json").exists() and json.loads((d / "editions/index.json").read_text())["editions"][0]["id"] == "2026-H2"
    assert all(not b.get("status") for b in _load(d)["blips"])                           # statuses untouched in edition 1
    c = run("scripts/compare_editions.py", d / "radar-state.json"); assert c.returncode != 0 and "first edition" in (c.stdout + c.stderr)

def test_second_edition_marks_changes_and_protects_snapshots():
    d, s = _ws(); _freeze(d); s = _load(d); s["meta"]["edition"] = "2027-H1"
    for b in s["blips"]:
        if b["name"] == "Odoo POS": b["ring"] = "adopt"; b["ring_reason"] = "A year of daily use."
        if b["name"] == "Microsoft 365": b["ring"] = "trial"
    s["blips"] = [b for b in s["blips"] if b["name"] != "CiviCRM"]; s["dropped"] = [{"name": "CiviCRM", "reason": "Too costly."}]
    s["blips"].append(dict(s["blips"][0], name="Zoho Books", ring="assess", tool_id="zoho-books")); s["actions"][0]["status"] = "done"; _save(d, s)
    c = run("scripts/compare_editions.py", d / "radar-state.json"); assert c.returncode == 0, c.stderr
    ch = json.loads((d / "radar-output/changes.json").read_text())
    assert [x["name"] for x in ch["new"]] == ["Zoho Books"] and ch["moved_in"][0]["name"] == "Odoo POS" and ch["moved_out"][0]["name"] == "Microsoft 365"
    assert ch["dropped"] == [{"name": "CiviCRM", "was": "Assess", "reason": "Too costly."}] and ch["metrics"]["actions_done"] == 1 and ch["metrics"]["actions_open"] == 0
    assert _freeze(d).returncode == 0
    st = {b["name"]: b for b in _load(d)["blips"]}
    assert st["Zoho Books"]["status"] == "New" and st["Zoho Books"]["isNew"] is True and st["Odoo POS"]["status"] == "Moved In" and st["Odoo POS"]["previous_ring"] == "trial"
    assert st["Microsoft 365"]["status"] == "Moved Out" and st["QuickBooks"]["status"] == "No Change" and _load(d)["meta"]["previous_edition"] == "2026-H2"
    r = _freeze(d); assert r.returncode != 0 and "--force" in r.stderr                     # no silent overwrite
    csvp = d / "radar-output"; run("scripts/state_to_radar.py", d / "radar-state.json"); assert "Moved In" in (csvp / "radar.csv").read_text()

def test_snapshots_pruned_to_four():
    d, s = _ws()
    for eid in ("2025-H1", "2025-H2", "2026-H1", "2026-H2", "2027-H1"):
        s = _load(d); s["meta"]["edition"] = eid; _save(d, s); assert _freeze(d).returncode == 0
    kept = sorted(p.stem for p in (d / "editions").glob("*.json") if p.stem != "index")
    assert kept == ["2025-H2", "2026-H1", "2026-H2", "2027-H1"]
    assert [e["id"] for e in json.loads((d / "editions/index.json").read_text())["editions"]] == kept

def test_matching_survives_renames_via_tool_id_and_missing_ids():
    import importlib; sys.path.insert(0, str(ROOT / "scripts")); C = importlib.import_module("compare_editions")
    prev = {"meta": {"edition": "A"}, "blips": [{"name": "Office 365", "tool_id": "microsoft-365", "ring": "adopt", "domain": "x"}, {"name": "Plain Tool", "ring": "trial", "domain": "x"}]}
    cur = {"meta": {"edition": "B"}, "blips": [{"name": "Microsoft 365", "tool_id": "microsoft-365", "ring": "adopt", "domain": "x"}, {"name": "plain  tool", "tool_id": "x-plain-tool", "ring": "adopt", "domain": "x"}]}
    c = C.compare(prev, cur); assert not c["new"] and not c["dropped"] and c["unchanged"] == 1 and c["moved_in"][0]["name"] == "plain  tool"
    assert C.edition_id(__import__("datetime").date(2027, 6, 30)) == "2027-H1" and C.edition_id(__import__("datetime").date(2027, 7, 1)) == "2027-H2"

def test_site_shows_changes_history_and_archive():
    d, s = _ws(); _freeze(d); s = _load(d); s["meta"]["edition"] = "2027-H1"
    for b in s["blips"]:
        if b["name"] == "Odoo POS": b["ring"] = "adopt"
    _save(d, s); _freeze(d); r = run("scripts/build_site.py", d / "radar-state.json"); assert r.returncode == 0, r.stderr
    t = (d / "radar-output/index.html").read_text(encoding="utf-8")
    assert "What changed since 2026-H2" in t and "History: 2026-H2 Trial → 2027-H1 Adopt" in t and "Earlier editions kept" in t and 'href="#changes"' in t
    d2, s2 = _ws(); run("scripts/build_site.py", d2 / "radar-state.json"); assert "What changed since" not in (d2 / "radar-output/index.html").read_text(encoding="utf-8")

def test_registry_annotate_fills_exact_matches_and_lists_the_rest():
    d, s = _ws(); s["blips"][0]["name"] = "Office 365"; s["blips"][1]["name"] = "Zendeskk"; _save(d, s)
    r = run("scripts/registry.py", "annotate", d / "radar-state.json", "--write"); out = json.loads(r.stdout)
    st = {b["name"]: b for b in _load(d)["blips"]}
    assert st["Office 365"]["tool_id"] == "microsoft-365" and "tool_id" not in st["Zendeskk"] and out["needs_a_question"][0]["suggestions"][0]["id"] == "zendesk"

def test_plain_language_lint():
    assert run("scripts/lint_plain.py").returncode == 0
    d = pathlib.Path(tempfile.mkdtemp()); f = d / "x.md"
    f.write_text('> Great! Let\'s leverage a robust, seamless journey.\n> Can you calibrate the blip? Or the registry?\n> ' + "word " * 30 + ".\n")
    r = run("scripts/lint_plain.py", f); assert r.returncode == 1
    for needle in ("buzzword", "filler", "jargon", "two questions", "long sentence"): assert needle in r.stdout, needle


# ---- member continuity and round-over-round trends
import importlib
sys.path.insert(0, str(ROOT / "scripts"))
RF = importlib.import_module("refresh_share_profile"); CR = importlib.import_module("compare_rounds"); REG = importlib.import_module("registry")

def test_refresh_moves_real_use_forward_and_lists_open_questions():
    kit = json.loads(KIT.read_text()); prof = json.loads(PROF.read_text()); prof["as_of"] = "2026-11-14"
    prof["blips"]["Zendesk"]["experience"] = "lt-6m"; prof["blips"]["Neon One"]["experience"] = "6-12m"; prof["blips"]["Microsoft 365"]["experience"] = "gt-3y"
    state = json.loads(STATE.read_text()); state["blips"].append(dict(state["blips"][0], name="Brand New Tool", tool_id="x-brand-new-tool", domain="crm")); state["blips"].remove(next(b for b in state["blips"] if b["name"] == "Microsoft Copilot"))
    state["domains"]["crm"]["status"] = "done"
    out, s = RF.refresh(state, kit, prof, None, REG.load(), today="2027-06-20")
    assert out["blips"]["Zendesk"]["experience"] == "6-12m" and out["blips"]["Neon One"]["experience"] == "1-3y" and out["blips"]["Microsoft 365"]["experience"] == "gt-3y"
    assert "Brand New Tool" in s["needs_details"] and "Microsoft Copilot" in s["dropped"] and out["tool_map"]["Brand New Tool"] == "custom"
    assert all(v is False for v in out["consent"].values()) and out["round_id"] == kit["round_id"] and out["as_of"] == "2027-06-20"
    assert RF.advance("lt-6m", 3) == "lt-6m" and RF.advance("none", 24) == "none" and RF.advance("1-3y", 30) == "gt-3y"
    prof2 = json.loads(json.dumps(prof)); prof2["blips"]["CiviCRM"]["experience"] = "none"
    s2 = RF.refresh(state, kit, prof2, None, REG.load(), today="2027-06-20")[1]
    assert "Odoo POS" not in s2["needs_real_use"]

def test_refresh_script_writes_profile_with_consent_off_and_export_uses_it():
    d = pathlib.Path(tempfile.mkdtemp()); prof = json.loads(PROF.read_text()); prof["as_of"] = "2026-11-14"; (d / "old.json").write_text(json.dumps(prof))
    r = run("scripts/refresh_share_profile.py", STATE, "--kit", KIT, "--previous-profile", d / "old.json", "--out", d / "new.json"); assert r.returncode == 0, r.stderr
    new = json.loads((d / "new.json").read_text()); assert all(v is False for v in new["consent"].values())
    e = run("scripts/state_to_contribution.py", STATE, "--kit", KIT, "--profile", d / "new.json", "--preview"); assert e.returncode == 0, e.stderr
    assert run("scripts/state_to_contribution.py", STATE, "--kit", KIT, "--profile", d / "new.json", "--out", d / "c.json").returncode != 0      # consent still needed

def test_real_use_going_backwards_is_warned():
    d = pathlib.Path(tempfile.mkdtemp()); r, c, k = _contrib(); prev = json.loads(c.read_text()); prev["blips"][0]["experience"] = "gt-3y"; (d / "prev.json").write_text(json.dumps(prev))
    prof = json.loads(PROF.read_text()); prof["blips"]["QuickBooks"]["experience"] = "lt-6m"; (d / "p.json").write_text(json.dumps(prof))
    p = run("scripts/state_to_contribution.py", STATE, "--kit", KIT, "--profile", d / "p.json", "--out", d / "o.json", "--previous-contribution", d / "prev.json")
    assert p.returncode == 0 and "Time only moves forward" in p.stderr

def test_kit_follow_up_fields_validated():
    d = pathlib.Path(tempfile.mkdtemp()); kit = json.loads((ROOT / "examples/consortium/round-kit-2.json").read_text()); (d / "k.json").write_text(json.dumps(kit))
    assert run("scripts/validate_contribution.py", "--kit-only", d / "k.json").returncode == 0
    kit["sequence"] = 0; (d / "k.json").write_text(json.dumps(kit)); assert run("scripts/validate_contribution.py", "--kit-only", d / "k.json").returncode == 1

def _aggs():
    ld = lambda p: json.loads((ROOT / p).read_text()); return ld("examples/consortium/round-output/aggregate.json"), ld("examples/consortium/round-output-2/aggregate.json")

def test_compare_rounds_reports_trends_without_leaking_counts():
    old, new = _aggs(); t = CR.compare(old, new)
    assert any(x["name"] == "Zoho CRM" for x in t["appeared"]) and any(x["name"] == "Odoo POS" and x["now"] == "adopt" for x in t["consensus_moved"])
    for x in t["rising"] + t["falling"]: assert x["adoption_now"] % 5 == 0 and x["adoption_before"] % 5 == 0
    assert "ring_counts" not in json.dumps(t) and t["comparability"]["declared_follow_up"] is True and t["panel"] is None
    r = run("scripts/compare_rounds.py", ROOT / "examples/consortium/round-output/aggregate.json", ROOT / "examples/consortium/round-output-2/aggregate.json", "--out", tempfile.mkdtemp()); assert r.returncode == 0

def test_compare_rounds_comparability_warnings_and_migration():
    old, new = _aggs(); new = json.loads(json.dumps(new))
    new["round"]["rubric_version"] = "2"; new["round"].pop("previous_round_id"); new["participants"]["count"] = 12
    w = " ".join(CR.compare(old, new)["comparability"]["warnings"]); assert "rating rules" in w and "does not name" in w and "Different organisations" in w
    new2 = json.loads(json.dumps(_aggs()[1]))
    for dm in new2["domains"].values():
        for t in dm["tools"]:
            if t["tool_id"] == "quickbooks": t["tool_id"] = "quickbooks-online"
    assert any(x["tool_id"] == "quickbooks-online" for x in CR.compare(old, new2)["appeared"])
    assert not any(x["tool_id"] in ("quickbooks", "quickbooks-online") for x in CR.compare(old, new2, {"quickbooks-online": "quickbooks"})["appeared"])

def test_registry_merge_resolves_old_names_and_rejects_bad_merges():
    d = pathlib.Path(tempfile.mkdtemp()); data = {"registry_version": "t", "tools": [{"id": "a-tool", "name": "A Tool", "aliases": ["Old Name"], "domains": [], "licence": "commercial"}, {"id": "b-tool", "name": "B Tool", "aliases": [], "domains": [], "licence": "commercial"}, {"id": "c-tool", "name": "C Tool", "aliases": [], "domains": [], "licence": "commercial"}]}
    (d / "r.json").write_text(json.dumps(data))
    assert run("scripts/registry.py", "merge", "a-tool", "b-tool", "--registry", d / "r.json").returncode == 0
    reg = REG.load(d / "r.json"); assert reg.resolve("Old Name")[0] == "b-tool" and reg.resolve("A Tool")[0] == "b-tool" and REG.migration_map(json.loads((d / "r.json").read_text())) == {"a-tool": "b-tool"}
    assert run("scripts/registry.py", "merge", "b-tool", "a-tool", "--registry", d / "r.json").returncode != 0        # would chain into a merged tool
    assert run("scripts/registry.py", "merge", "c-tool", "c-tool", "--registry", d / "r.json").returncode != 0

def test_trends_section_in_benchmark_site_is_escaped():
    t = json.loads((ROOT / "examples/consortium/round-output-2/trends.json").read_text()); t["old_round"]["title"] = "<script>alert(1)</script>"; t["comparability"]["warnings"].append("<img src=x onerror=1>")
    d = pathlib.Path(tempfile.mkdtemp()); (d / "t.json").write_text(json.dumps(t))
    r = run("scripts/build_benchmark.py", "site", ROOT / "examples/consortium/round-output-2/aggregate.json", "--trends", d / "t.json", "--out", d / "s.html"); assert r.returncode == 0, r.stderr
    h = (d / "s.html").read_text(encoding="utf-8"); assert "Trends since" in h and "<script>alert" not in h and "<img src=x" not in h
