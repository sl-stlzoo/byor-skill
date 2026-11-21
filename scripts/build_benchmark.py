#!/usr/bin/env python3
"""Build the consortium benchmark site and private per-member reports from aggregate.json.  (stdlib only; no network; hardened like build_site.py)

  python scripts/build_benchmark.py site   round-output/aggregate.json [--narrative narrative.json] [--trends trends.json] [--out round-output/benchmark/index.html]
  python scripts/build_benchmark.py member round-output/aggregate.json --contribution inbox/x.json --kit round-kit.json [--out FILE]
  python scripts/build_benchmark.py members round-output/aggregate.json --inbox inbox/ --kit round-kit.json   # one report per accepted contribution
The ONLY inputs are aggregate.json (k-suppressed, anonymised) plus, for member reports, that member's own contribution. Raw files of other
organisations are never read here. A narrative is validated: strict fields, no markup/URLs, links only to benchmarked tools, and it must not contain
the name of any anonymous contributor (checked against _convener/anon-names.json when present).
"""
import argparse, base64, hashlib, html, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import registry as R
import validate_contribution as V
import aggregate_round as A
from build_site import esc, slug, CREDIT

RING_LABEL = {"adopt": "Adopt", "trial": "Trial", "assess": "Assess", "caution": "Caution", "split": "Split"}
EXP_LABEL = V.VOCAB["experience_labels"]
CSS = """:root{--bg:#fbfaf7;--ink:#1c1b19;--mute:#5d5a54;--line:#dedad1;--card:#fff;--ac:#0f766e;--r0:#0f766e;--r1:#2563eb;--r2:#b45309;--r3:#be123c}
@media(prefers-color-scheme:dark){:root{--bg:#12110f;--ink:#f1eee8;--mute:#a8a39a;--line:#35322d;--card:#1a1815;--ac:#5eead4;--r0:#5eead4;--r1:#93c5fd;--r2:#fbbf24;--r3:#fda4af}}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:70px}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 Georgia,serif;overflow-wrap:anywhere}nav{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:4px max(16px,calc((100vw - 1060px)/2))}.skip{position:fixed;left:12px;top:-100px;background:var(--card);padding:8px 12px;z-index:10}.skip:focus{top:8px}main{max-width:1100px;margin:0 auto;padding:0 20px 60px}
h1,h2,h3,button,.ui,table,summary,nav{font-family:system-ui,-apple-system,"Segoe UI",sans-serif}h1{font-size:clamp(30px,5vw,52px);line-height:1.08;margin:.3em 0}h2{font-size:26px;margin:0 0 .5em}h3{font-size:19px;margin:1.4em 0 .4em}
section{padding:40px 0;border-bottom:1px solid var(--line)}.eyebrow{font:600 13px system-ui;letter-spacing:.14em;text-transform:uppercase;color:var(--ac);padding-top:48px}.lede{color:var(--mute);max-width:70ch}
.stats{display:flex;gap:12px;flex-wrap:wrap}.stat{border:1px solid var(--line);background:var(--card);border-radius:12px;padding:10px 16px}.stat b{display:block;font:700 26px system-ui}.stat span{font:13px system-ui;color:var(--mute)}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:15px}th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--mute)}
.chip{display:inline-block;font:600 12px system-ui;border:1px solid var(--line);border-radius:99px;padding:2px 9px;background:var(--card);margin:0 4px 4px 0}.c-adopt{color:var(--r0);border-color:var(--r0)}.c-trial{color:var(--r1);border-color:var(--r1)}.c-assess{color:var(--r2);border-color:var(--r2)}.c-caution{color:var(--r3);border-color:var(--r3)}
.bar{display:flex;height:10px;border-radius:5px;overflow:hidden;background:var(--line);min-width:110px}.bar i{display:block}.b-adopt{background:var(--r0)}.b-trial{background:var(--r1)}.b-assess{background:var(--r2)}.b-caution{background:var(--r3)}
.tools{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}button{font:600 13px system-ui;border:1px solid var(--line);background:var(--card);color:var(--ink);padding:7px 13px;border-radius:99px;cursor:pointer}button.on{background:var(--ink);color:var(--bg)}
input,select{font:15px system-ui;padding:8px 12px;border-radius:99px;border:1px solid var(--line);background:var(--card);color:var(--ink)}.note{color:var(--mute);font-size:14px}.hide{display:none!important}
.card{border:1px solid var(--line);background:var(--card);border-radius:14px;padding:16px 18px;margin:12px 0;max-width:75ch}details{margin:4px 0}summary{cursor:pointer;font-size:14px}a{color:var(--ac)}.priv{border:2px solid var(--r3);border-radius:12px;padding:10px 14px;font:600 14px system-ui}
footer{padding:30px 0;color:var(--mute);font:14px system-ui}@media(max-width:600px){main{padding-inline:16px}section{padding:28px 0}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr))}}@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;transition-duration:.01ms!important}}@media print{.tools,nav{display:none!important}body{background:#fff;color:#000}section{break-inside:avoid-page}}:focus-visible{outline:3px solid var(--ac);outline-offset:2px}"""


def page(title, body, script="", noindex=True):
    sp = ("'sha256-%s'" % base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()) if script else "'none'"
    csp = f"default-src 'none'; script-src {sp}; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'"
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)}</title>'
            f'<meta name="color-scheme" content="light dark"><meta http-equiv="Content-Security-Policy" content="{csp}">' + ('<meta name="robots" content="noindex, nofollow">' if noindex else "")
            + f"<style>{CSS}</style></head><body><a class='skip' href='#main'>Skip to content</a><nav aria-label='Page sections'><div class='tools'><a href='#highlights'>Highlights</a><a href='#domains'>Domains</a><a href='#participants'>Participants</a><a href='#method'>Method</a></div></nav><main id='main'>{body}</main>" + (f"<script>{script}</script>" if script else "") + "</body></html>")


NAMES = {"crm": "CRM", "erp": "ERP", "hris": "HRIS", "gis": "GIS", "itsm-helpdesk": "ITSM Helpdesk", "ai-tools": "AI Tools", "e-commerce": "E-commerce", "food-and-beverage": "Food & Beverage", "call-center": "Call Center"}


def dom_name(d): return NAMES.get(d, d.replace("-", " ").title())


def bar(counts, n):
    segs = "".join(f'<i class="b-{r}" style="width:{100 * counts.get(r, 0) / n:.0f}%"></i>' for r in A.RING_ORDER if counts.get(r)) if n else ""
    return f'<div class="bar" title="{esc(", ".join(f"{RING_LABEL[r]} {counts.get(r, 0)}" for r in A.RING_ORDER))}">{segs}</div>'


def chip(r): return f'<span class="chip c-{esc(r)}">{esc(RING_LABEL.get(r, r))}</span>'


def check_narrative(nar, agg, anon_names):
    E = []
    if not isinstance(nar, dict) or set(nar) - {"headline", "themes"}: return ["narrative: only 'headline' and 'themes' keys allowed"]
    tools = {t["name"].lower() for d in agg["domains"].values() for t in d["tools"]}
    texts = [nar.get("headline", "")]
    if len(nar.get("headline", "")) > 160: E.append("headline too long (160 max)")
    th = nar.get("themes", [])
    if not isinstance(th, list) or len(th) > 4: E.append("themes: at most 4")
    for i, t in enumerate(th if isinstance(th, list) else []):
        if not isinstance(t, dict) or set(t) != {"title", "body"} or not isinstance(t["body"], list) or len(t["body"]) > 4: E.append(f"themes[{i}]: needs title and 1-4 body paragraphs"); continue
        if len(t["title"]) > 80: E.append(f"themes[{i}].title too long")
        texts += [t["title"]] + t["body"]
        for p in t["body"]:
            if not isinstance(p, str) or len(p) > 600: E.append(f"themes[{i}]: paragraph over 600 chars")
    for s in texts:
        if re.search(r"[<>`\x00-\x08\x0b-\x1f]|https?:|www\.|@|\{\{", s or ""): E.append("narrative contains markup, URLs or '@'")
        for tk in re.findall(r"\[\[(.+?)\]\]", s or ""):
            if tk.lower() not in tools: E.append(f"narrative links [[{tk}]] which is not a benchmarked tool")
        for n in anon_names:
            if n.lower() in (s or "").lower(): E.append("narrative mentions an anonymous contributor; remove the name")
    return sorted(set(E))


def link_tools(text, agg):
    names = {t["name"].lower(): t["name"] for d in agg["domains"].values() for t in d["tools"]}
    return re.sub(r"\\\[\\\[(.+?)\\\]\\\]", lambda m: f'<a href="#t-{slug(names.get(html.unescape(m.group(1)).lower(), ""))}">{m.group(1)}</a>' if html.unescape(m.group(1)).lower() in names else m.group(1), esc(text).replace("[[", "\\[\\[").replace("]]", "\\]\\]"))


def comp_table(title, d):
    return f'<div class="card"><b class="ui">{esc(title)}</b><table>' + "".join(f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in d.items()) + "</table></div>"


def trends_html(t):
    cw = "".join(f'<p class="priv">{esc(w)}</p>' for w in t["comparability"]["warnings"])
    li = lambda rows, fmt: "<ul>" + "".join(f"<li>{esc(fmt(x))}</li>" for x in rows) + "</ul>" if rows else '<p class="note">None.</p>'
    pts = lambda x: f"{x['name']}: {x['adoption_before']}% to {x['adoption_now']}% ({x['change_points']:+d} points)"
    return (f'<section id="trends"><h2>Trends since {esc(t["old_round"]["title"])}</h2><p class="lede">{t["old_round"]["organisations"]} organisations before, {t["new_round"]["organisations"]} now. Adoption is shown in steps of 5 points, and only for tools shown in both rounds.</p>{cw}'
            '<div class="scroll"><table><tr><th>Rising adoption</th><th>Falling adoption</th><th>Peer rating moved</th><th>New in the benchmark</th><th>No longer shown</th></tr><tr>'
            f'<td>{li(t["rising"][:8], pts)}</td><td>{li(t["falling"][:8], pts)}</td><td>{li(t["consensus_moved"][:8], lambda x: f"{x['name']}: {RING_LABEL.get(x['before'], x['before'])} to {RING_LABEL.get(x['now'], x['now'])}")}</td>'
            f'<td>{li(t["appeared"][:8], lambda x: x["name"])}</td><td>{li(t["no_longer_shown"][:8], lambda x: x["name"])}</td></tr></table></div></section>')


def site(agg, nar=None, anon_names=(), trends=None):
    r, p, k = agg["round"], agg["participants"], agg["round"]["min_cohort"]
    all_tools = [(d, t) for d, v in agg["domains"].items() for t in v["tools"]]
    hl = lambda pred, n=6: sorted([x for x in all_tools if pred(x[1])], key=lambda x: (-x[1]["n_orgs"], x[1]["name"]))[:n]
    li = lambda items, extra="": "".join(f'<li><a href="#t-{slug(t["name"])}">{esc(t["name"])}</a> <span class="note">({t["n_orgs"]} orgs{extra(t) if callable(extra) else ""})</span></li>' for d, t in items) or "<li class='note'>None at this round's thresholds.</li>"
    body = [f'<div class="eyebrow">{esc(r["convener"])} · round {esc(r["id"])} · {esc(r["generated"])}</div><h1>{esc(r["title"])}</h1>',
            f'<p class="lede">An informal benchmark of what organisations like yours actually use and how they rate it. Nothing is shown unless at least {k} organisations contributed it. Opinions, not audits.</p>',
            f'<div class="stats"><div class="stat"><b>{p["count"]}</b><span>organisations</span></div><div class="stat"><b>{len(all_tools)}</b><span>tools benchmarked</span></div>'
            f'<div class="stat"><b>{sum(d["long_tail_suppressed"] for d in agg["domains"].values())}</b><span>tools below the minimum (hidden)</span></div><div class="stat"><b>{agg["normalisation"]["adjusted_ratings"]}</b><span>ratings reinterpreted</span></div></div>']
    if nar:
        body.append(f'<section id="narrative"><h2>What the round says</h2>' + (f'<p class="lede">{esc(nar.get("headline", ""))}</p>' if nar.get("headline") else "")
                    + "".join(f'<div class="card"><h3>{esc(t["title"])}</h3>' + "".join(f"<p>{link_tools(x, agg)}</p>" for x in t["body"]) + "</div>" for t in nar.get("themes", [])) + "</section>")
    body.append('<section id="highlights"><h2>Highlights</h2><div class="scroll"><table><tr><th>Peer consensus: Adopt</th><th>Contested</th><th>Caution watch</th><th>Emerging</th></tr><tr>'
                f'<td><ul>{li(hl(lambda t: t.get("consensus") == "adopt" and t.get("agreement", 0) >= 0.6))}</ul></td><td><ul>{li(hl(lambda t: "contested" in t.get("flags", [])))}</ul></td>'
                f'<td><ul>{li(hl(lambda t: "caution-watch" in t.get("flags", [])))}</ul></td><td><ul>{li(hl(lambda t: "emerging" in t.get("flags", [])))}</ul></td></tr></table></div></section>')
    if trends: body.append(trends_html(trends))
    body.append('<section id="domains"><h2>By domain</h2><div class="tools" role="toolbar" aria-label="Filter"><button class="on" data-r="all">All</button>' + "".join(f'<button data-r="{x}">{RING_LABEL[x]}</button>' for x in A.RING_ORDER)
                + '<input id="q" type="search" placeholder="Search tools" aria-label="Search tools"></div>')
    for d, v in agg["domains"].items():
        nm = dom_name(d)
        if v["suppressed"]: body.append(f'<h3 class="dom">{esc(nm)}</h3><p class="note dom">Fewer than {k} organisations assessed this domain, so it is not shown.</p>'); continue
        rows = ""
        for t in v["tools"]:
            cons = t.get("consensus"); n_b = t["n_basis"]; basis = "" if t["basis"] == "all" else f'<div class="note">based on {n_b} named org{"s" if n_b != 1 else ""}</div>'
            named = "".join(f'<li>{esc(x["org"])}: {chip(x["ring"])} {esc(EXP_LABEL[x["experience"]])}, {esc(x["scale"].replace("-", " "))}' + (f' <span class="note">“{esc(x["rationale"])}”</span>' if x.get("rationale") else "") + "</li>" for x in t["named_ratings"])
            tags = ", ".join(f'{esc(a)} ({b})' for a, b in t.get("caution_tags", {}).items())
            rows += (f'<tr class="trow" id="t-{slug(t["name"])}" data-c="{esc(cons or "")}" data-n="{esc(t["name"].lower())}"><td><b>{esc(t["name"])}</b><div class="note">{esc(t["licence"])}</div></td>'
                     f'<td>{t["n_orgs"]} of {esc(v["orgs_covering"])} ({int(t["adoption_share"] * 100)}%)</td><td>{chip(cons) if cons else ""}{"".join(f"<span class=chip>{esc(f)}</span>" for f in t.get("flags", []))}{basis}</td>'
                     f'<td>{bar(t.get("ring_counts", {}), n_b)}</td><td>{esc(tags) or "-"}</td><td>' + (f"<details><summary>{len(t['named_ratings'])} named</summary><ul>{named}</ul></details>" if named else "-") + "</td></tr>")
        body.append(f'<h3 class="dom">{esc(nm)} <span class="note">· {esc(v["orgs_covering"])} organisations</span></h3><div class="scroll dom"><table><tr><th>Tool</th><th>Used by</th><th>Peer rating</th><th>Spread</th><th>Cautions</th><th>Who</th></tr>{rows}</table></div>'
                    + (f'<p class="note dom">{v["long_tail_suppressed"]} further tool(s) used by fewer than {k} organisations are hidden.</p>' if v["long_tail_suppressed"] else ""))
    body.append("</section>")
    body.append(f'<section id="participants"><h2>Who took part</h2><p>{", ".join(esc(n) for n in p["named"]) or "No named organisations"}' + (f' and {p["anonymous_count"]} anonymous organisation(s).' if p["anonymous_count"] else ".") + '</p><div class="stats">'
                + comp_table("Sector", p["composition"]["sector"]) + comp_table("Size (staff)", p["composition"]["size_band"]) + comp_table("Region", p["composition"]["region"]) + "</div></section>")
    sl = "".join(f'<h3>{esc(dim.title())}: {esc(val)} <span class="note">({s["orgs"]} orgs)</span></h3><p>' + ", ".join(f'{esc(t["name"])} ({RING_LABEL[t["consensus"]]})' for t in s["tools"][:12]) + "</p>" for dim, vals in agg["slices"].items() for val, s in vals.items() if s["tools"])
    if sl: body.append(f'<section id="slices"><h2>By sector and region</h2><p class="note">Only groups with at least {k} organisations.</p>{sl}</section>')
    body.append('<section id="method"><h2>How to read this, and the privacy rules</h2><ul>' + "".join(f"<li>{esc(x)}</li>" for x in agg["normalisation"]["rules"])
                + f'</ul><p class="note">Rings follow the canonical radar idea: Adopt is proven here, Trial needs real use, Assess is being explored, Caution reflects a negative experience. Each organisation also reported how strict its own rings are; see the calibration data in the download. '
                f'Anonymous contributors are never named. Named organisations agreed to be shown against their ratings. This is an informal benchmark of opinions, not a vendor ranking, audit or endorsement.</p>'
                f'<p><a download="aggregate.json" href="data:application/json;base64,{base64.b64encode(json.dumps(agg, ensure_ascii=False).encode()).decode()}">Download aggregate.json</a></p></section>')
    body.append(f'<footer>Generated with {esc(CREDIT)}. Method adapted from the Thoughtworks Technology Radar; not affiliated with or endorsed by Thoughtworks.</footer>')
    script = ("(()=>{const q=s=>[...document.querySelectorAll(s)];let ring='all',term='';const ap=()=>q('.trow').forEach(r=>r.classList.toggle('hide',!((ring==='all'||r.dataset.c===ring)&&r.dataset.n.includes(term))));"
              "q('button[data-r]').forEach(b=>b.onclick=()=>{ring=b.dataset.r;q('button[data-r]').forEach(x=>x.classList.toggle('on',x===b));ap()});document.getElementById('q').oninput=e=>{term=e.target.value.toLowerCase().trim();ap()}})();")
    return page(r["title"], "".join(body), script)


def member(agg, c, kit):
    k = kit["min_cohort"]; org = c["contributor"]["org_name"]
    idx = {t["tool_id"]: (d, t) for d, v in agg["domains"].items() for t in v["tools"]}
    rk = {x: i for i, x in enumerate(A.RING_ORDER)}; rows = []; mine = set(); notb = 0; align = diff = 0
    for b in c["blips"]:
        mine.add(b["tool_id"]); eff, adj = A.effective(b["ring"], b["experience"])
        if b["tool_id"] not in idx: notb += 1; continue
        d, t = idx[b["tool_id"]]; cons = t.get("consensus")
        if cons in rk: delta = rk[eff] - rk[cons]; lab = "Aligned" if delta == 0 else ("More confident than peers" if delta < 0 else "More cautious than peers"); align += delta == 0; diff += delta != 0
        else: lab = "Peers split" if cons == "split" else "Peer breakdown limited"
        rows.append(f'<tr><td><b>{esc(t["name"])}</b></td><td>{chip(eff)}' + (f' <span class="note">(you said {esc(RING_LABEL[b["ring"]])}; counted as {esc(RING_LABEL[eff])} given {esc(EXP_LABEL[b["experience"]])})</span>' if adj else "") + f'</td><td>{chip(cons) if cons else ""} <span class="note">{t["n_orgs"]} orgs</span></td><td>{esc(lab)}</td></tr>')
    miss = [(d, t) for d in c["domains_covered"] if d in agg["domains"] and not agg["domains"][d]["suppressed"] for t in agg["domains"][d]["tools"] if t["adoption_share"] >= 0.5 and t["tool_id"] not in mine]
    warn = [(d, t) for tid, (d, t) in idx.items() if tid in mine and ("caution-watch" in t.get("flags", []) or t.get("consensus") == "caution")]
    li = lambda xs: "".join(f'<li><b>{esc(t["name"])}</b> <span class="note">{esc(dom_name(d))} · {t["n_orgs"]} orgs ({int(t["adoption_share"] * 100)}%)</span></li>' for d, t in xs) or '<li class="note">None.</li>'
    calib = "".join(f'<tr><td>{esc(f.replace("_", " "))}</td><td><b>{esc(c["calibration"][f])}</b></td><td class="note">' + ", ".join(f"{esc(v)}: {esc(n)}" for v, n in agg["calibration"][f].items()) + "</td></tr>" for f in V.VOCAB["calibration"])
    body = (f'<div class="eyebrow">Private report · {esc(agg["round"]["title"])}</div><h1>{esc(org)} vs the round</h1><p class="priv">Private to {esc(org)}. It contains your own contribution and k-anonymous round aggregates only; no other organisation\'s raw data.</p>'
            f'<div class="stats"><div class="stat"><b>{len(c["blips"])}</b><span>your tools shared</span></div><div class="stat"><b>{align}</b><span>aligned with peers</span></div><div class="stat"><b>{diff}</b><span>differ from peers</span></div><div class="stat"><b>{notb}</b><span>not benchmarked (&lt;{k} orgs)</span></div></div>'
            f'<section><h2>Your tools vs the peer consensus</h2><div class="scroll"><table><tr><th>Tool</th><th>Your rating</th><th>Peers</th><th>Comparison</th></tr>{"".join(rows)}</table></div></section>'
            f'<section><h2>Widely used by peers, not in your radar</h2><p class="note">Used by at least half of the organisations that assessed the same domain.</p><ul>{li(miss)}</ul></section>'
            f'<section><h2>You use these; peers are cautious</h2><ul>{li(warn)}</ul></section>'
            f'<section><h2>How strict are your rings compared with peers?</h2><div class="scroll"><table><tr><th>Question</th><th>You</th><th>All organisations</th></tr>{calib}</table></div></section>'
            f'<footer>Generated with {esc(CREDIT)}. Opinions, not audits. Cells below {k} show “&lt;k”.</footer>')
    return page(f"{org} vs the round", body)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["site", "member", "members"]); ap.add_argument("aggregate"); ap.add_argument("--narrative"); ap.add_argument("--trends"); ap.add_argument("--out")
    ap.add_argument("--contribution"); ap.add_argument("--kit"); ap.add_argument("--inbox"); ap.add_argument("--registry"); ap.add_argument("--anon-names"); a = ap.parse_args()
    agg = json.loads(pathlib.Path(a.aggregate).read_text(encoding="utf-8")); base = pathlib.Path(a.aggregate).resolve().parent
    if a.mode == "site":
        nar = None; anon = []
        an = pathlib.Path(a.anon_names or base / "_convener" / "anon-names.json")
        if an.exists(): anon = json.loads(an.read_text(encoding="utf-8"))
        if a.narrative:
            nar = json.loads(pathlib.Path(a.narrative).read_text(encoding="utf-8")); E = check_narrative(nar, agg, anon)
            if E: sys.exit("Narrative rejected:\n  " + "\n  ".join(E))
        out = pathlib.Path(a.out or base / "benchmark" / "index.html"); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(site(agg, nar, anon, json.loads(pathlib.Path(a.trends).read_text(encoding="utf-8")) if a.trends else None), encoding="utf-8"); print("Wrote", out)
    else:
        if not a.kit: sys.exit("--kit required")
        kit = json.loads(pathlib.Path(a.kit).read_text(encoding="utf-8")); reg = R.load(a.registry)
        files = [pathlib.Path(a.contribution)] if a.mode == "member" else sorted(pathlib.Path(a.inbox).glob("*.json"))
        for f in files:
            c = json.loads(f.read_text(encoding="utf-8")); E, _ = V.validate(c, kit, reg)
            if E: print("skip", f.name, "(invalid)"); continue
            out = pathlib.Path(a.out) if (a.out and a.mode == "member") else base / "member-reports" / f"{slug(c['contributor']['org_name'])}.html"
            out.parent.mkdir(parents=True, exist_ok=True); out.write_text(member(agg, c, kit), encoding="utf-8"); print("Wrote", out)


if __name__ == "__main__":
    main()
