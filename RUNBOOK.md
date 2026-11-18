# Runbook: from zip to a working, evaluated radar skill set

Follow in order. Each step has a check; do not continue until it passes. Time: about 30 minutes plus one test run.

## Part 1. Stand up the repo

1. **Create the repo.** GitHub > New repository. Any name works (this runbook shows `byor-skill`); you will pass your chosen name to `set_owner.py` in step 3 and every file follows it. **Public**
   (raw links and Pages cannot be fetched by AI clients from a private repo). Do not add a README, licence or .gitignore (the zip has them).
   Check: empty repo page shows "Quick setup".
2. **Unpack locally.** `unzip byor-skill.zip && cd byor-skill`. Check: `ls` shows `AGENTS.md`, `skills/`, `config/`, `index.html`, `.nojekyll`.
3. **Personalise (owner, repo name, ref).** `python scripts/set_owner.py sl-stlzoo [REPO] [BRANCH]`
   This replaces the `sl-stlzoo` placeholder and writes absolute file URLs into `AGENTS.md` (needed because many chat tools only fetch URLs they have seen).
   Check: `grep -c raw.githubusercontent.com AGENTS.md` returns 30 or more; `grep -rn sl-stlzoo README.md index.html` shows nothing except code comments.
3b. **Security gate (do not skip).** `bash scripts/audit.sh` must print `AUDIT RESULT: PASS`. Read `SECURITY.md` §9. For anything beyond a personal trial,
   pin to a reviewed commit: `python scripts/set_owner.py sl-stlzoo REPO <full-commit-sha>` after your first push, then use the SHA-pinned raw URLs in prompts.
4. **Rebuild the single-file bundle.** `python scripts/build_bundle.py`. Check: prints `Wrote .../BUNDLE.md` (about 160 KB).
5. **Local tests.** `pip install pyyaml pytest && python scripts/check_config.py && pytest -q tests`. Check: config OK, 7 passed.
6. **Push.**
   ```
   git init -b main && git add -A && git commit -m "Initial import"
   git remote add origin https://github.com/sl-stlzoo/byor-skill.git
   git push -u origin main
   ```
   Check: Actions tab shows the `validate` workflow green. If it fails on "BUNDLE.md is stale", rerun step 4 and commit.
7. **Enable Pages (only if you want a public landing page).** Pages is public on most plans, even for a private repo; the landing page contains no secrets, but never put radar data in this repo. Settings > Pages > Source "Deploy from a branch" > `main` / `/ (root)` > Save. Wait 1-3 minutes.
   Check: `https://sl-stlzoo.github.io/byor-skill/` shows the landing page and the prompt contains your name.
8. **Run the deploy check** (needs internet). `python scripts/verify_deploy.py sl-stlzoo`. Check: `RESULT: READY`.
   Also open the raw `AGENTS.md` link in a browser and confirm it is plain text with the absolute URL block at the end.
9. **Tag it.** `git tag v1.0.0 && git push --tags`. Test against a tag-pinned copy later so results are reproducible.

## Part 2. Use and evaluate it in the Claude app

Use a brand-new chat for every run (old context contaminates results). Turn on web search/fetch in the chat's tools menu.
If you want files and the site built in chat, also enable **Code execution and file creation** in Settings > Capabilities.

**Route A: paste the prompt (primary).**
```
Fetch https://raw.githubusercontent.com/sl-stlzoo/byor-skill/main/AGENTS.md and follow it exactly to guide me, one question
at a time, through building my own Thoughtworks BYOR technology radar and a single-page website. Save progress as you go.
```
Expected: a short welcome and one question (depth). If it says it cannot fetch the file, go to Route B.

**Route B: single-file bundle (most reliable for fetching; core `BUNDLE.md` is about 25k tokens, `BUNDLE-FULL.md` is about 70k).** Same prompt with `.../BUNDLE.md` and the sentence
"It contains every instruction file; follow AGENTS.md inside it." If the reply seems to ignore later phases, the fetch
may have been truncated: go to Route C.

**Route C: attach the zip (most reliable overall).** Attach `byor-skill.zip` (code execution on) and say:
"Unzip this, read AGENTS.md, and guide me through building my radar, one question at a time." The agent can then run the
scripts and produce `index.html` for real. Download outputs from the chat when finished.

**Route D: native skills (experimental, not verified).** Each folder in `skills/` has a valid `SKILL.md`, but skills
reference `config/`, `templates/` and `scripts/` at the repo root, which a skills upload would not carry. Prefer A to C until you test this.

## Part 3. Evaluate (use `TESTING.md`)

1. Pre-flight: Part 1 step 8 reads READY.
2. Run the scripted 45-minute protocol in `TESTING.md` through Route A, then Route C (two runs, fresh chats).
3. Score checks A-F. Record the result row (date, client version, model, route, mode, checks, notes).
4. Resume test: end the first run after the first quadrant, copy the saved state, start a new chat, resume.
5. Update `TESTING.md` and the table in `index.html`, then `python scripts/build_bundle.py` if any skill text changed, commit, push.

## Part 5. Run a consortium round (optional)
Convener: follow `docs/CONSORTIUM.md` and the `byor-radar-convene` skill (design kit and roster, collect files in `inbox/`, aggregate, narrative, site and private reports, delete raw files on the charter date). Members: run the normal workflow, then Phase 11 (`byor-radar-share`). Use the zip route (Route C) for both so the scripts and the tool registry are on disk. Pilot with the fictional data in `examples/consortium/` first.

## Renaming or moving later
Re-run `python scripts/set_owner.py NEW_OWNER NEW_REPO [REF]`: it reads the old values from `project.json`, rewrites them everywhere (docs, landing page, prompts, evals, URL block), rebuilds `BUNDLE.md`, and updates `project.json`. Then commit, push, rename the repo on GitHub, and run `python scripts/verify_deploy.py`. `python scripts/set_owner.py --show` prints the current values.

## Part 4. Change safely

- Edit config/skills > `pytest -q tests && python scripts/check_config.py` > `python scripts/build_bundle.py` > commit > push > rerun `verify_deploy.py`.
- Never edit `BUNDLE.md` or the URL block in `AGENTS.md` by hand; regenerate.
- After each change retest with a fresh chat; tag releases (`v1.0.1`) so you know which version produced which result.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Claude says it cannot access the URL | Repo must be public; confirm the raw link opens in a private browser window; use Route B or C |
| It fetches AGENTS.md but not the other files | The absolute URL block is missing: rerun step 3, rebuild bundle, push |
| Landing page 404 | Pages not enabled or still building; check Settings > Pages and the Actions "pages build" run |
| Raw file shows old content | Raw links cache for a few minutes; wait, or append `?v=2` to the URL in the prompt |
| Asks you to paste state / prints CSV instead of saving files | Normal when file creation is off: it is in chat-snapshot mode. Enable code execution or accept snapshots |
| Site not built in chat | No code execution or scripts unavailable: use Route C |
| `verify_deploy` says placeholder sl-stlzoo present | Rerun `set_owner.py` then `build_bundle.py` and push |
| CI fails: bundle stale | `python scripts/build_bundle.py`, commit |
