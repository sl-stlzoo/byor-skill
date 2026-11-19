#!/usr/bin/env bash
# Self-service security audit of this repo. Read-only; makes no network calls. Run from any directory.
#   bash scripts/audit.sh        Exit 1 if a check fails. Read the output; do not just trust the exit code.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"; FAIL=0
ok(){ echo "PASS  $1"; }; bad(){ echo "FAIL  $1"; FAIL=1; }; info(){ echo "INFO  $1"; }

echo "== 1. Scripts: dangerous primitives (expected: only verify_deploy.py uses the network) =="
HITS=$(grep -nE "^\s*(import|from)\s+(subprocess|socket|http|urllib|requests|ctypes|pickle|marshal|shutil|tempfile)|os\.system|os\.popen|\beval\(|\bexec\(|__import__" scripts/*.py | grep -v "^scripts/verify_deploy.py" || true)
[ -z "$HITS" ] && ok "no process-spawn, eval/exec, deserialisation or network code in scripts (excluding verify_deploy.py)" || { bad "unexpected primitives:"; echo "$HITS"; }
grep -nE "\beval\b|\bsource\b|curl |wget |\| *(ba)?sh( |$)" $(ls scripts/*.sh | grep -v audit.sh) >/dev/null && bad "shell eval/source/curl/wget/pipe-to-shell found in scripts/*.sh" || ok "no eval, source, curl, wget or pipe-to-shell in shell scripts"
python3 - <<'PY' || FAIL=1
import ast, pathlib, sys
allowed = {"argparse","base64","csv","datetime","hashlib","html","io","json","math","os","re","shlex","sys","collections","pathlib","importlib","urllib","yaml","runpy","json","difflib","compare_editions","registry","validate_contribution","aggregate_round","build_benchmark","build_site"}
bad = []
for p in pathlib.Path("scripts").glob("*.py"):
    for n in ast.walk(ast.parse(p.read_text())):
        mods = [a.name.split(".")[0] for a in n.names] if isinstance(n, ast.Import) else ([n.module.split(".")[0]] if isinstance(n, ast.ImportFrom) and n.module else [])
        bad += [f"{p}: {m}" for m in mods if m not in allowed and m not in {"state_to_radar","compare_editions","registry","validate_contribution","aggregate_round","build_benchmark","build_site"}]
print("PASS  scripts import only the standard library (plus PyYAML for config checks and the question bank)" if not bad else "FAIL  non-stdlib imports: " + ", ".join(bad)); sys.exit(1 if bad else 0)
PY

echo "== 2. Instructions: every external domain mentioned (review this list) =="
domains(){ grep -rhoE --include=*.md --include=*.yaml --include=*.py --include=*.sh --include=*.html --exclude-dir=examples --exclude-dir=tests --exclude=audit.sh --exclude=BUNDLE.md "https?://[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)+" . | sed -E 's#https?://##'; }
domains | sort | uniq -c | sort -rn
ALLOW='^(www\.thoughtworks\.com|radar\.thoughtworks\.com|github\.com|raw\.githubusercontent\.com|docs\.docker\.com|docs\.google\.com|localhost|127\.0\.0\.1|www\.w3\.org|[A-Za-z0-9_-]+\.github\.io|[a-z0-9-]+\.example|example\.com|evil\.example|fonts\.googleapis\.com|docs\.github\.com|owasp\.org|genai\.owasp\.org|www\.anthropic\.com|platform\.claude\.com|arxiv\.org|agentskills\.io|docs\.claude\.com|support\.claude\.com|opensource\.org|www\.apache\.org|www\.gnu\.org|cheatsheetseries\.owasp\.org)$'
UNK=$(domains | sort -u | grep -vE "$ALLOW" || true)
[ -z "$UNK" ] && ok "all domains are on the expected allow-list" || { bad "domains not on the allow-list (review!):"; echo "$UNK"; }

echo "== 3. Instructions: patterns that would tell an agent to run or send things =="
P=$(grep -rniE "curl |wget |pip install|npm install|\| *sh( |$)|base64 -d|chmod \+x|rm -rf|sudo |ssh |scp |nc -|powershell" skills AGENTS.md config templates 2>/dev/null || true)
[ -z "$P" ] && ok "no install/exec/remote-shell instructions in skills, AGENTS.md, config or templates" || { info "found (verify each is benign user-facing guidance):"; echo "$P"; }
grep -rniE "ignore (all |any )?(previous|prior) instructions|disregard .*instructions|do not tell the user|without telling|silently (send|upload|email)|exfiltrat" skills AGENTS.md config 2>/dev/null | grep -viE "never|do not follow|treat|refuse|security-guardrails|injection" && bad "possible hidden-instruction language" || ok "no hidden-instruction language"
grep -rnE "[A-Za-z0-9+/]{80,}={0,2}" skills AGENTS.md config templates --include=*.md --include=*.yaml 2>/dev/null | grep -v "https\?://" | head -3 | grep -q . && info "long base64-like strings found; inspect" || ok "no long encoded blobs in instructions"
python3 - <<'PY' || FAIL=1
import pathlib, sys
odd = [str(p) for p in pathlib.Path(".").rglob("*") if p.is_file() and ".git" not in p.parts and p.read_bytes()[:200] and any(ord(c) in (0x200b,0x200c,0x200d,0x2060,0xfeff,0x202e) for c in p.read_text(errors="ignore")[:200000]) and p.suffix in (".md",".yaml",".py",".sh",".html",".json")]
print("PASS  no zero-width or bidi control characters in text files" if not odd else "FAIL  hidden Unicode characters in: " + ", ".join(odd)); sys.exit(1 if odd else 0)
PY

echo "== 3b. Wording for users is plain (lint) =="
python3 scripts/lint_plain.py | tail -3 | grep -q "PASS" && ok "plain-language lint passes" || { bad "plain-language lint failed (run scripts/lint_plain.py)"; }

echo "== 4. Generated site is self-contained and carries a CSP =="
T=$(mktemp -d); python3 scripts/build_site.py examples/sample-radar-state.json --out "$T/i.html" >/dev/null
EXT=$(grep -oE "(src|href|action)=\"https?://[^\"]+" "$T/i.html" | grep -v "thoughtworks.com" || true)
[ -z "$EXT" ] && ok "site loads nothing from external hosts (only outbound links to thoughtworks.com docs)" || { bad "external references:"; echo "$EXT"; }
grep -q "Content-Security-Policy" "$T/i.html" && grep -q "default-src 'none'" "$T/i.html" && ok "CSP present (default-src 'none', script hash)" || bad "CSP missing"
grep -qiE "<script[^>]+src=|@import|fetch\(|XMLHttpRequest|WebSocket|sendBeacon|localStorage|document\.cookie" "$T/i.html" && bad "site contains network/storage primitives" || ok "site has no fetch/XHR/WebSocket/beacon/localStorage/cookie use"
rm -rf "$T"

echo "== 5. Repo hygiene =="
[ -f SECURITY.md ] && ok "SECURITY.md present" || bad "SECURITY.md missing"
python3 -c "import json;c=json.load(open('project.json'));assert all(k in c for k in ('owner','repo','branch'))" 2>/dev/null && ok "project.json valid (owner, repo, branch)" || bad "project.json missing or invalid"
[ -f .gitignore ] && grep -q "radar-state.json" .gitignore && ok ".gitignore keeps your radar data out of the repo" || bad ".gitignore does not exclude radar-state.json"
find . -type f -not -path "./.git/*" | sed 's#^\./##' | awk 'END{print "INFO  "NR" files in repo"}'
[ "$(find . -type f -size +300k -not -path './.git/*' | wc -l)" -eq 0 ] && ok "no large (>300 KB) files" || info "large files present (BUNDLE.md is expected to be ~160 KB)"

echo; [ $FAIL -eq 0 ] && echo "AUDIT RESULT: PASS" || echo "AUDIT RESULT: FAIL (review items above)"; exit $FAIL
