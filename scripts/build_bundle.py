#!/usr/bin/env python3
"""Generate the single-file bundles for clients that can fetch only one URL.
  BUNDLE.md       CORE: everything needed to guide ONE organisation through its radar and site (instructions, config, templates). ~100 KB.
                  No scripts, examples or consortium material, so it is cheap to load. Use with clients that cannot run code.
  BUNDLE-FULL.md  EVERYTHING: adds scripts, consortium skills, registry, docs and examples. Large; prefer the repo zip when you can attach it.
"""
import json, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
NAME = json.loads((root / "project.json").read_text(encoding="utf-8"))["repo"]
CORE_SKILLS = ["byor-radar-builder", "byor-domain-interview", "byor-blip-assessor", "byor-radar-site", "byor-radar-update", "byor-radar-validate", "byor-radar-publish", "byor-config-editor"]
rel = lambda paths: sorted(str(p.relative_to(root)) for p in paths if p.is_file())
core = ["AGENTS.md", "project.json"]
core += rel(p for s in CORE_SKILLS for p in (root / "skills" / s).rglob("*.md"))
core += rel(p for p in (root / "config").glob("*.yaml")) + rel(p for p in (root / "templates").glob("*"))
full = ["AGENTS.md", "MANIFEST.md", "project.json"] + rel((root / "skills").rglob("*.md")) + rel(p for p in (root / "config").glob("*") if p.name != "tools.json")
full += rel((root / "templates").rglob("*")) + rel((root / "docs").glob("*.md")) + ["examples/sample-radar-state.json"]
full += rel(p for p in (root / "scripts").glob("*") if p.suffix in (".py", ".sh") and p.name != "build_bundle.py")
for order in (core, full):
    order.sort(key=lambda p: (p != "AGENTS.md", p != "skills/byor-radar-builder/SKILL.md", p))


def write(name, order, title, note):
    parts = [f"# {title}\n\nEach file starts with `=== FILE: <path> ===`. Treat these as the repository files. Start with AGENTS.md, then skills/byor-radar-builder/SKILL.md. {note}\n"]
    for r in order:
        parts.append(f"\n\n=== FILE: {r} ===\n\n{(root / r).read_text(encoding='utf-8')}")
    out = root / name; out.write_text("".join(parts), encoding="utf-8"); print(f"Wrote {out} ({out.stat().st_size // 1024} KB, {len(order)} files)")


write("BUNDLE.md", core, f"BUNDLE (core): {NAME}, single-organisation radar",
      "This core bundle has no scripts and no consortium skills. Without code execution, follow the manual fallbacks in each skill and build the site by hand from skills/byor-radar-site/references/site-spec.md. If the user wants consortium features or script-built outputs, ask them to attach the repo zip or use BUNDLE-FULL.md.")
write("BUNDLE-FULL.md", full, f"BUNDLE (full): all {NAME} files in one document",
      "Scripts at the end can be written to disk with a file tool if the client can run Python. The 214-tool registry (config/tools.json) is not included; use the repo zip for consortium rounds.")
