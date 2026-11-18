#!/usr/bin/env python3
"""Plain-language lint for the words the agent says to users (stdlib only).

  python scripts/lint_plain.py [paths...]      default: skills/ and templates/
Checks every user-facing line (blockquotes starting with '>' and double-quoted questions or statements) outside code fences for:
banned buzzwords and chatbot filler, internal jargon, and sentences longer than 25 words. Exit 1 on any finding.
The style rules live in skills/byor-radar-builder/references/plain-language.md.
"""
import pathlib, re, sys

BANNED = r"leverage|delve|robust|seamless|holistic|synerg|ecosystem|streamline|empower|unlock|deep dive|journey|navigate|harness|tapestry|elevate|cutting-edge|best-in-class|paradigm|touch base|circle back|bandwidth|actionable|learnings|utili[sz]e|facilitate|granular|pain point|north star|low-hanging|game-changer|landscape|stakeholder|ideate|onboard|take it to the next level|moving forward"
FILLER = r"^(great|awesome|absolutely|certainly|sure thing|perfect)[!,. ]|i'd be happy to|i would be happy to|let's dive|dive into|as an ai|i hope this helps"
JARGON = r"\bblips?\b|rubric|calibrat|evidence mode|laddering|\bregistry\b|taxonom|\bpersona\b|ontology|\bschema\b|\bpayload\b|\bartifact\b|\bheuristic|\bcohort\b|normali[sz]"
MAX_WORDS = 25


def user_facing(text):
    fence = False
    for n, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"): fence = not fence; continue
        if fence: continue
        s = line.strip()
        if s.startswith(">"): yield n, s.lstrip("> ").strip()
        for m in re.finditer(r'(?<![\w`])"([^"`\n]{14,}?)"(?![\w`])', line):
            q = m.group(1)
            if re.search(r"[?.!]$", q) and " " in q and not re.search(r"[{}\[\]=_/\\]|\.(md|json|yaml|py)\b", q): yield n, q


def check(path):
    out = []
    for n, s in user_facing(pathlib.Path(path).read_text(encoding="utf-8")):
        plain = re.sub(r"<[^>]+>|\*\*|\*|`", "", s)
        if re.search(BANNED, plain, re.I): out.append((n, "buzzword: " + re.search(BANNED, plain, re.I).group(0), s))
        if re.search(FILLER, plain, re.I): out.append((n, "filler: " + re.search(FILLER, plain, re.I).group(0), s))
        if re.search(JARGON, plain, re.I): out.append((n, "jargon: " + re.search(JARGON, plain, re.I).group(0), s))
        if plain.count("?") > 1 and not s.startswith("-"): out.append((n, "two questions in one message", s))
        for sent in re.split(r"(?<=[.?!])\s+", plain):
            if len(sent.split()) > MAX_WORDS: out.append((n, f"long sentence ({len(sent.split())} words)", s)); break
    return out


def main():
    root = pathlib.Path(__file__).resolve().parent.parent
    paths = [pathlib.Path(a) for a in sys.argv[1:]] or [root / "skills", root / "templates"]
    files = [f for p in paths for f in ([p] if p.is_file() else sorted(p.rglob("*.md"))) if f.name != "plain-language.md"]   # that file quotes bad examples on purpose
    bad = 0
    for f in files:
        for n, why, s in check(f):
            bad += 1; print(f"{f.relative_to(root) if f.is_absolute() and root in f.parents else f}:{n}: {why}\n    {s[:150]}")
    print("PLAIN-LANGUAGE LINT:", "PASS" if not bad else f"{bad} finding(s)"); return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
