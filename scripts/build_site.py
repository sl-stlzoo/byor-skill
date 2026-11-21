#!/usr/bin/env python3
"""Build a single-file, self-contained static site (index.html) from radar-state.json.  (stdlib only)

Usage:  python scripts/build_site.py radar-state.json [--out radar-output/index.html] [--theme theme.json] [--accent "#0f766e"] [--public]
No network requests, no external fonts or scripts. Core content works without JavaScript; JS adds filtering,
quadrant zoom and a theme toggle. Default is <meta name="robots" content="noindex">; pass --public to allow indexing.
"""
import argparse, base64, csv, datetime, hashlib, html, io, json, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_editions as CE
from state_to_radar import build_rows, neutralise
try: CREDIT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project.json"), encoding="utf-8")).get("credit", "byor-skill")
except (OSError, ValueError): CREDIT = "byor-skill"

SECTORS = [(-90, 0), (-180, -90), (90, 180), (0, 90)]          # quadrant 1..4 : top-right, top-left, bottom-left, bottom-right
VIEWBOXES = [(400, 0, 400, 400), (0, 0, 400, 400), (0, 400, 400, 400), (400, 400, 400, 400)]
RING_FRAC = [0.0, 0.34, 0.62, 0.84, 1.0]
CX = CY = 400; R = 372
RING_COPY = {
    "adopt": "Proven here and mature. Not using it, where it fits, would be a poor and slightly irresponsible choice.",
    "trial": "Used for real work, in a limited way. We want to learn whether it earns a place in the toolkit.",
    "assess": "Interesting and worth a closer look. We are learning, not yet relying on it.",
    "hold": "We have had a negative experience, or see real risk. Consider alternatives and avoid starting new work with it.",
}


def esc(s): return html.escape(str(s or ""), quote=True)
def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "blip"
def h(s): return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def clean_html(s):
    """Allow-list sanitiser. Every tag is replaced by a placeholder (allowed tags are rebuilt from scratch, others dropped);
    ALL remaining text, including any stray '<' or '>', is HTML-escaped; then placeholders are restored."""
    s = re.sub(r"<(script|style|iframe|object|embed)[^>]*>.*?</\1>", "", s or "", flags=re.S | re.I)
    keep = []
    def tag(m):
        t, rest = m.group(2).lower(), m.group(3)
        out = ""
        if t in {"b", "i", "strong", "em", "br", "code", "ul", "ol", "li", "p"}: out = f"<{m.group(1)}{t}>"
        elif t == "a" and m.group(1): out = "</a>"
        elif t == "a":
            u = re.search(r'href\s*=\s*"(https?://[^"\s<>]+)"', rest)
            out = f'<a href="{esc(u.group(1))}" rel="noopener noreferrer">' if u else ""
        keep.append(out); return f"\x00{len(keep)-1}\x00"
    s = re.sub(r"<(/?)\s*([a-zA-Z0-9]+)([^>]*)>", tag, s)
    s = html.escape(s.replace("\x00", "\x01"), quote=False).replace("\x01", "\x00")
    return re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], s)


def layout(state):
    qs, rings, blips = state["quadrants"], state["rings"], state["blips"]
    qi = {q["id"]: i for i, q in enumerate(qs)}; ri = {r["id"]: i for i, r in enumerate(rings)}
    rorder = lambda b: (qi.get(b["quadrant"], 9), ri.get(b["ring"], 9), b["name"].lower())
    ordered = sorted(blips, key=rorder)
    for n, b in enumerate(ordered, 1): b["_n"] = n
    groups = {}
    for b in ordered: groups.setdefault((qi[b["quadrant"]], ri[b["ring"]]), []).append(b)
    for (q, r), g in groups.items():
        a0, a1 = SECTORS[q]; r0, r1 = RING_FRAC[r] * R, RING_FRAC[r + 1] * R
        pts = []
        for k, b in enumerate(g):
            frac = b["radial"] if isinstance(b.get("radial"), (int, float)) else 0.2 + 0.6 * h(b["name"] + "r")
            rad = r0 + (r1 - r0) * (0.12 + 0.76 * min(max(frac, 0), 1))
            ang = a0 + (a1 - a0) * (0.08 + 0.84 * ((k + 0.5 + (h(b["name"]) - 0.5) * 0.5) / len(g)))
            pts.append([rad, ang])
        for _ in range(80):                                   # simple relaxation to reduce overlaps
            xy = [(CX + p[0] * math.cos(math.radians(p[1])), CY + p[0] * math.sin(math.radians(p[1]))) for p in pts]
            for i in range(len(pts)):
                for j in range(i + 1, len(pts)):
                    dx, dy = xy[j][0] - xy[i][0], xy[j][1] - xy[i][1]; d = math.hypot(dx, dy) or 0.1
                    if d < 30:
                        push = (30 - d) / 2 / 4
                        pts[i][1] -= math.copysign(push / max(pts[i][0], 1) * 57.3, dx * 0 + (1 if pts[j][1] > pts[i][1] else -1) * -1)
                        pts[j][1] += math.copysign(push / max(pts[j][0], 1) * 57.3, (1 if pts[j][1] > pts[i][1] else -1))
                        pts[i][0] += (-1 if dy > 0 else 1) * push * 0.3; pts[j][0] += (1 if dy > 0 else -1) * push * 0.3
            for p in pts:
                p[0] = min(max(p[0], r0 + 17), r1 - 17) if r1 - r0 > 36 else (r0 + r1) / 2
                p[1] = min(max(p[1], a0 + 5), a1 - 5)
        for b, p in zip(g, pts):
            b["_x"] = CX + p[0] * math.cos(math.radians(p[1])); b["_y"] = CY + p[0] * math.sin(math.radians(p[1]))
    return ordered


def shape(b, q):
    st = (b.get("status") or "").lower()
    x, y, n = b["_x"], b["_y"], b["_n"]
    if b.get("isNew") or st == "new": d = f'<path d="M{x:.1f} {y-14:.1f} L{x+13:.1f} {y+10:.1f} L{x-13:.1f} {y+10:.1f}Z" class="sh"/>'; ty = y + 6
    elif st in ("moved in", "moved out"): d = f'<path d="M{x:.1f} {y-14:.1f} L{x+14:.1f} {y:.1f} L{x:.1f} {y+14:.1f} L{x-14:.1f} {y:.1f}Z" class="sh"/>'; ty = y + 4
    else: d = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="12.5" class="sh"/>'; ty = y + 4
    return (f'<a href="#b-{slug(b["name"])}" class="blip q{q}" data-q="{q}" data-ring="{esc(b["ring"])}" data-name="{esc(b["name"].lower())}" aria-label="Blip {n}: {esc(b["name"])}; {esc(b["_ringname"])}">'
            f'<title>{n}. {esc(b["name"])} ({esc(b["_ringname"])})</title><circle cx="{x:.1f}" cy="{y:.1f}" r="19" class="hit"/><g class="marker">{d}<text x="{x:.1f}" y="{ty:.1f}">{n}</text></g></a>')


def svg_radar(state, ordered):
    qs, rings = state["quadrants"], state["rings"]
    o = ['<svg id="radar" viewBox="0 0 800 800" role="group" aria-label="Radar chart; the same content is listed below" xmlns="http://www.w3.org/2000/svg">']
    for i in range(3, -1, -1):
        o.append(f'<circle cx="{CX}" cy="{CY}" r="{RING_FRAC[i+1]*R:.0f}" class="band b{i}"/>')
    o.append(f'<line x1="{CX-R}" y1="{CY}" x2="{CX+R}" y2="{CY}" class="axis"/><line x1="{CX}" y1="{CY-R}" x2="{CX}" y2="{CY+R}" class="axis"/>')
    for i, r in enumerate(rings):
        mid = (RING_FRAC[i] + RING_FRAC[i + 1]) / 2 * R
        for sx in (1, -1):
            o.append(f'<text x="{CX+sx*mid:.0f}" y="{CY+4}" class="ringlbl" text-anchor="middle">{esc(r["_name"].upper())}</text>')
    # Put quadrant titles in the corners with a generous inset. Use tspans so
    # long custom names wrap instead of being clipped by the SVG viewBox.
    for i, q in enumerate(qs):
        left, top = i in (1, 2), i in (0, 1)
        x, y, anchor = (24 if left else 776), (42 if top else 758), ("start" if left else "end")
        words = str(q["name"]).split()
        lines, line = [], ""
        for word in words:
            if line and len(line) + len(word) + 1 > 23:
                lines.append(line); line = word
            else:
                line = (line + " " + word).strip()
        if line: lines.append(line)
        tspans = "".join(f'<tspan x="{x}" dy="{0 if n == 0 else 20}">{esc(text)}</tspan>' for n, text in enumerate(lines[:3]))
        o.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="qlbl q{i}">{tspans}</text>')
    o += [shape(b, [q["id"] for q in qs].index(b["quadrant"])) for b in ordered]
    o.append("</svg>")
    return "\n".join(o)


def link_text(text, names):
    out = esc(text)
    def rep(m):
        n = m.group(1).strip(); k = next((x for x in names if x.lower() == html.unescape(n).lower()), None)
        return f'<a class="bliplink" href="#b-{slug(k)}">{esc(k)}</a>' if k else n
    return re.sub(r"\[\[(.+?)\]\]", rep, out)


def csv_uri(rows):
    rows = [neutralise(r) for r in rows]
    buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    return "data:text/csv;charset=utf-8;base64," + base64.b64encode(buf.getvalue().encode()).decode()


THEME_DEFAULTS = {"mode": "system", "accent": "#d6453d", "q0": "#287d70",
                  "q1": "#aa641d", "q2": "#7955a2", "q3": "#b23e62"}


def theme_config(theme=None, accent=None):
    if theme is None:
        theme = {}
    if not isinstance(theme, dict) or set(theme) - THEME_DEFAULTS.keys():
        raise ValueError("Theme must be an object with optional mode, accent, q0, q1, q2 and q3 keys.")
    result = {**THEME_DEFAULTS, **theme}
    if accent is not None:
        result["accent"] = accent
    if result["mode"] not in ("system", "light", "dark"):
        raise ValueError("Theme mode must be system, light or dark.")
    for key in THEME_DEFAULTS.keys() - {"mode"}:
        color = result[key]
        if not isinstance(color, str) or not re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", color):
            raise ValueError(f"Theme {key} must be a hex colour such as #d6453d.")
        if len(color) == 4:
            color = "#" + "".join(c * 2 for c in color[1:])
        result[key] = color.lower()
    return result


def build(state, accent, public, changes=None, snaps=None, archive=None, theme=None):
    branding = theme_config(theme, accent)
    m = state["meta"]; today = datetime.date.today()
    for r in state["rings"]:
        r["_name"] = (m.get("hold_label") or "Caution") if r["id"] == "hold" else r["name"]
    rn = {r["id"]: r["_name"] for r in state["rings"]}
    for b in state["blips"]: b["_ringname"] = rn[b["ring"]]
    qs, rings = state["quadrants"], state["rings"]; qids = [q["id"] for q in qs]
    ordered = layout(state); names = [b["name"] for b in ordered]
    org = m.get("organization") or "Our organisation"; title = m.get("site_title") or m.get("radar_title") or f"{org} Technology Radar"
    edition = m.get("edition") or "Edition 1"
    pub = m.get("published") or today.isoformat()
    try: pub_label = datetime.date.fromisoformat(pub[:10]).strftime("%B %Y")
    except ValueError: pub_label = pub
    tagline = m.get("tagline") or "An opinionated guide to the software we use, trial, explore and question"
    counts = {r["id"]: sum(1 for b in ordered if b["ring"] == r["id"]) for r in rings}
    n_new = sum(1 for b in ordered if b.get("isNew") or (b.get("status") or "").lower() == "new")
    n_moved = sum(1 for b in ordered if (b.get("status") or "").lower() in ("moved in", "moved out"))
    intro = m.get("intro") or (f"This radar is a snapshot of the software {org} uses, is trialling, is exploring, and is wary of. "
        "It is built from our own experience, so it is an opinion, not a market survey, a vendor ranking or a list of approved products.")
    uses_radial = any(isinstance(b.get("radial"), (int, float)) for b in ordered)
    rows = build_rows(state); csvu = csv_uri(rows)
    jsonu = "data:application/json;charset=utf-8;base64," + base64.b64encode(json.dumps(rows, indent=2, ensure_ascii=False).encode()).decode()

    ring_cards = "".join(
        f'<li class="ringcard r{i}"><h3>{esc(r["_name"])} <span class="count">{counts[r["id"]]}</span></h3><p>{esc(RING_COPY[r["id"]])}</p>'
        + ("<ul>" + "".join(f"<li>{esc(c)}</li>" for c in r.get("criteria", [])[:4]) + "</ul>" if r.get("criteria") else "") + "</li>"
        for i, r in enumerate(rings))
    themes = ""
    for t in state.get("themes", []):
        refs = [n for n in names if re.search(r"\[\[" + re.escape(n) + r"\]\]", " ".join(t.get("body", [])), re.I)] or t.get("blips", [])
        themes += (f'<article class="theme"><h3>{esc(t["title"])}</h3>' + "".join(f"<p>{link_text(p, names)}</p>" for p in t.get("body", []))
                   + ('<p class="chips">' + "".join(f'<a class="chip" href="#b-{slug(n)}">{esc(n)}</a>' for n in refs if n in names) + "</p>" if refs else "") + "</article>")
    themes_sec = (f'<section id="themes"><h2>Themes for this edition</h2><p class="lede">Patterns we noticed across the blips we discussed. They form the story of this radar.</p>{themes}</section>' if themes else "")
    stat_sec = "".join(f'<div class="stat"><b>{counts[r["id"]]}</b><span>{esc(r["_name"])}</span></div>' for r in rings)
    cards = ""
    for qi_, q in enumerate(qs):
        cards += f'<section class="qsec" data-q="{qi_}" id="q-{esc(q["id"])}"><h3 class="qh q{qi_}">{esc(q["name"])}</h3>'
        for r in rings:
            bl = [b for b in ordered if b["quadrant"] == q["id"] and b["ring"] == r["id"]]
            if not bl: continue
            cards += f'<h4 class="rh">{esc(r["_name"])}</h4><div class="grid">'
            for b in bl:
                st = b.get("status") or ("New" if b.get("isNew") else "")
                meta = " · ".join(x for x in [esc(state["domains"].get(b.get("domain", ""), {}).get("name") or (b.get("domain") or "").replace("-", " ").title()),
                                              ("Owner: " + esc(b["owner"])) if b.get("owner") else "", ("Reviewed " + esc(b["last_reviewed"])) if b.get("last_reviewed") else ""] if x)
                cards += (f'<article class="card" id="b-{slug(b["name"])}" data-q="{qi_}" data-ring="{esc(b["ring"])}" data-name="{esc(b["name"].lower())}">'
                          f'<h5><span class="num q{qi_}">{b["_n"]}</span>{esc(b["name"])}</h5>'
                          f'<p class="tags"><span class="tag">{esc(r["_name"])}</span>' + (f'<span class="tag st">{esc(st)}</span>' if st else "") + (f'<span class="tag">was {esc(CE.LABEL.get(b["previous_ring"], b["previous_ring"]))}</span>' if b.get("previous_ring") and b["previous_ring"] != b["ring"] else "") + f'</p>'
                          f'<div class="desc">{clean_html(b.get("description", ""))}</div><p class="meta">{meta}</p>' + (lambda h: f'<p class="meta">History: {" → ".join(esc(e + " " + r_) for e, r_ in h)}</p>' if len({r_ for _, r_ in h}) > 1 else "")(CE.history(snaps, state, b) if snaps else []) + '</article>')
            cards += "</div>"
        cards += "</section>"
    changes_sec = changes_nav = archive_html = ""
    if changes:
        li_ = lambda items, fmt: "<ul>" + "".join(f"<li>{esc(fmt(x))}</li>" for x in items) + "</ul>" if items else '<p class="note">None.</p>'
        mv = lambda x: f"{x['name']}: {x['from']} to {x['to']}" + (f". {x['reason']}" if x.get("reason") else "")
        mt = changes["metrics"]
        changes_sec = (f'<section id="changes"><h2>What changed since {esc(changes["previous"])}</h2><p class="lede">{len(changes["new"])} new, {len(changes["moved_in"])} moved toward Adopt, {len(changes["moved_out"])} moved toward Caution, {len(changes["dropped"])} dropped, {changes["unchanged"]} unchanged.</p>'
                       '<ul class="ringcards">'
                       f'<li class="ringcard"><h3>New</h3>{li_(changes["new"], lambda x: f"{x['name']} (now {x['ring']})")}</li>'
                       f'<li class="ringcard"><h3>Moved toward Adopt</h3>{li_(changes["moved_in"], mv)}</li>'
                       f'<li class="ringcard"><h3>Moved toward Caution</h3>{li_(changes["moved_out"], mv)}</li>'
                       f'<li class="ringcard"><h3>Dropped</h3>{li_(changes["dropped"], lambda x: f"{x['name']} (was {x['was']})" + (f". {x['reason']}" if x.get("reason") else ""))}</li></ul>'
                       f'<p class="note">Actions: {mt["actions_done"]} done, {mt["actions_open"]} open. Reviews overdue: {len(mt["overdue_reviews"])}.</p></section>')
        changes_nav = '<a href="#changes">Changes</a>'
    if archive:
        archive_html = "<p>Earlier editions kept: " + ", ".join(esc(f'{e["id"]} ({e["tools"]} tools)') for e in archive) + ".</p>"
    actions = state.get("actions", [])
    act_sec = ('<section id="actions"><h2>Decisions and actions</h2><div class="scroll"><table><thead><tr><th>Action</th><th>Tool</th><th>Owner</th><th>By</th></tr></thead><tbody>'
               + "".join(f'<tr><td>{esc(a.get("action"))}</td><td>{esc(a.get("tool"))}</td><td>{esc(a.get("owner"))}</td><td>{esc(a.get("by"))}</td></tr>' for a in actions)
               + "</tbody></table></div></section>") if actions else ""
    contrib = m.get("contributors") or []
    contrib_html = ("<p>" + " · ".join(esc(c["name"] + (f' ({c["role"]})' if c.get("role") else "")) if isinstance(c, dict) else esc(c) for c in contrib) + "</p>") if contrib else f"<p>Prepared by {esc(m.get('owner') or org)}.</p>"
    q_tabs = '<button class="tab on" data-view="all">All</button>' + "".join(f'<button class="tab" data-view="{i}">{esc(q["name"])}</button>' for i, q in enumerate(qs))
    r_chips = "".join(f'<button class="chip tog on" data-ring="{esc(r["id"])}">{esc(r["_name"])}</button>' for r in rings)
    faq = [
        ("What is this radar?", f"A snapshot of software at {org}, grouped into four quadrants and four rings. It records what we have actually experienced. It is not a market survey and makes no attempt to cover every product."),
        ("Is it a list of approved software?", "No. It is a shared view that helps people prioritise learning and decisions. Settled tools we are happy with may be missing because nothing about them is changing."),
        ("How are the rings decided?", "By discussion and evidence. A blip reaches Trial only with real use on real work. Adopt is reserved for things where not using them, in the right context, would be a poor choice. Caution means we have had a negative experience."),
        ("What do position and shape mean?", "Quadrants are just topic areas; a blip’s angle inside its quadrant means nothing. " + ("Distance from the centre inside a ring does matter: closer to the inner edge means more confidence. " if uses_radial else "") + "Triangles are new this edition, diamonds moved ring, circles are unchanged."),
        ("Why is a tool I know missing?", "No one nominated it, it did not change since last time, it was cut to keep the radar readable, or we covered a more general idea instead."),
        ("How do blips change?", "Blips move between rings as our experience grows, and may be dropped after an edition if nothing new happened. Older editions stay in our archive and are not updated."),
        ("How do I suggest something?", m.get("how_to_nominate") or "Tell the radar owner what you use, with a short note on how it went. We ask for real experience; a good demo is enough for Assess only."),
        ("How often is it updated?", f"{m.get('cadence') or 'Regularly'}. Next review: {m.get('next_review') or 'to be scheduled'}."),
    ]
    faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faq)
    keep = "".join(f"<li>{x}</li>" for x in [
        f"<b>Start with Adopt.</b> Are you using each one where it applies? If not, ask why.",
        f"<b>Read {esc(rings[-1]['_name'])} carefully.</b> If you rely on any of these, plan to reflect and consider moving away.",
        "<b>Then Trial.</b> Learn about the ones relevant to you and see what a trial would take.",
        "<b>Assess last.</b> Worth knowing about, but lower in priority unless it fits your situation perfectly."])
    noindex = "" if public else '<meta name="robots" content="noindex, nofollow">'
    script = re.search(r"<script>(.*?)</script>", TEMPLATE, re.S).group(1)
    digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    csp = ("default-src 'none'; script-src 'sha256-%s'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'" % digest)
    palette = ";".join(f"--brand-{key}:{branding[key]}" for key in THEME_DEFAULTS if key != "mode")
    values = {
        "TITLE": esc(title), "ORG": esc(org), "EDITION": esc(edition), "PUBLISHED": esc(pub_label), "TAGLINE": esc(tagline), "INTRO": esc(intro),
        "NOINDEX": noindex, "PALETTE": palette, "MODE": branding["mode"], "TABS": q_tabs, "RCHIPS": r_chips, "SVG": svg_radar(state, ordered), "STATS": stat_sec,
        "CSP": f'<meta http-equiv="Content-Security-Policy" content="{csp}">',
        "NEW": str(n_new), "MOVED": str(n_moved), "TOTAL": str(len(ordered)), "RINGCARDS": ring_cards, "THEMES": themes_sec, "CARDS": cards, "ACTIONS": act_sec,
        "KEEP": keep, "FAQ": faq_html, "CONTRIB": contrib_html, "CREDIT": esc(CREDIT), "CHANGES": changes_sec, "CHANGESNAV": changes_nav, "ARCHIVE": archive_html, "CSV": csvu, "JSON": jsonu, "ISO": today.isoformat(),
        "NEXTREVIEW": esc(m.get("next_review") or "to be scheduled"),
    }
    out = re.sub(r"%%([A-Z]+)%%", lambda m: values[m[1]], TEMPLATE)
    warns = []
    for t in state.get("themes", []):
        for tok in re.findall(r"\[\[(.+?)\]\]", " ".join(t.get("body", []))):
            if tok.lower() not in [n.lower() for n in names]: warns.append(f"theme '{t['title']}' links unknown blip [[{tok}]]")
    if not state.get("themes"): warns.append("no themes: the narrative is the heart of a canonical radar; run Phase 7 (byor-radar-site)")
    if not m.get("contributors"): warns.append("no contributors listed")
    return out, warns


TEMPLATE = r'''<!doctype html>
<html lang="en" data-theme="%%MODE%%" style="%%PALETTE%%"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>%%TITLE%%</title><meta name="description" content="%%TAGLINE%%"><meta name="color-scheme" content="light dark">%%CSP%%%%NOINDEX%%
<!-- Generated %%ISO%% by %%CREDIT%%. Method inspired by the Thoughtworks Technology Radar (https://www.thoughtworks.com/radar/faq). Not affiliated with Thoughtworks. -->
<style>
 :root{color-scheme:light;--bg:#fff;--ink:#171717;--mute:#525252;--line:#d4d4d4;--card:#fff;--soft:#f5f6f4;--shade:#000;--bi:#fff;--band0:#0000000d;--band1:#00000009;--band2:#00000006;--band3:#00000003}
:root[data-theme=dark]{color-scheme:dark;--bg:#121212;--ink:#f5f5f5;--mute:#b5b5b5;--line:#404040;--card:#202020;--soft:#181818;--shade:#fff;--bi:#121212;--band0:#ffffff14;--band1:#ffffff0e;--band2:#ffffff09;--band3:#ffffff05}
@media(prefers-color-scheme:dark){:root[data-theme=system]{color-scheme:dark;--bg:#121212;--ink:#f5f5f5;--mute:#b5b5b5;--line:#404040;--card:#202020;--soft:#181818;--shade:#fff;--bi:#121212;--band0:#ffffff14;--band1:#ffffff0e;--band2:#ffffff09;--band3:#ffffff05}}
:root{--accent:color-mix(in srgb,var(--brand-accent) 46%,var(--shade));--q0:color-mix(in srgb,var(--brand-q0) 46%,var(--shade));--q1:color-mix(in srgb,var(--brand-q1) 46%,var(--shade));--q2:color-mix(in srgb,var(--brand-q2) 46%,var(--shade));--q3:color-mix(in srgb,var(--brand-q3) 46%,var(--shade))}
 *{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:76px}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif;overflow-wrap:anywhere;-webkit-tap-highlight-color:#d6453d30}
h1,h2,h3,h4,h5,.ui,button,nav,.tag,.meta,table,summary{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--accent)}main,header .in,footer .in{max-width:1100px;margin:0 auto;padding:0 20px}
 .skip{position:fixed;left:12px;top:-100px;background:var(--card);padding:8px 12px;z-index:20;border:1px solid var(--line);border-radius:8px}.skip:focus{top:8px}
nav.top{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);font-size:14px}
 nav.top .in{display:flex;gap:18px;align-items:center;overflow-x:auto;white-space:nowrap;padding:10px 20px;max-width:1100px;margin:auto;scrollbar-width:thin}nav.top a{text-decoration:none;color:var(--mute)}nav.top a:hover{color:var(--ink)}nav.top button{margin-left:auto}
header.hero{padding:64px 0 36px;border-bottom:1px solid var(--line);background:radial-gradient(ellipse at 5% 0%,color-mix(in srgb,var(--brand-accent) 20%,transparent),transparent 64%),var(--soft)}.eyebrow{font:600 13px system-ui;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}
h1{font-size:clamp(34px,6vw,64px);line-height:1.05;margin:.3em 0 .2em;letter-spacing:-.02em}.tag-line{font-size:clamp(18px,2.4vw,24px);color:var(--mute);margin:0 0 20px;max-width:46ch}
.lede{color:var(--mute);max-width:68ch}.intro{max-width:68ch;font-size:19px}
.btns{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.btn,button{font:600 14px system-ui;border:1px solid var(--line);background:var(--card);color:var(--ink);padding:9px 14px;border-radius:8px;cursor:pointer;text-decoration:none;touch-action:manipulation}.btn.pri{background:var(--accent);border-color:var(--accent);color:var(--bi)}
.btn:hover,button:hover{outline:2px solid var(--accent);outline-offset:1px}button:disabled{opacity:.55;cursor:not-allowed}h1,h2,h3{text-wrap:balance}
h2{font-size:clamp(26px,3.4vw,36px);margin:0 0 .4em;letter-spacing:-.01em}section{padding:52px 0;border-bottom:1px solid var(--line)}
.stats{display:flex;gap:14px;flex-wrap:wrap;margin:26px 0 0}.stat{border:1px solid var(--line);border-radius:12px;padding:10px 16px;background:var(--card);min-width:96px}.stat b{display:block;font:700 26px system-ui}.stat span{font:13px system-ui;color:var(--mute)}
.tools{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0 14px}.tab.on,.chip.tog.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}.chip.tog{font-weight:500}
input[type=search]{font:15px system-ui;padding:9px 14px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--ink);min-width:200px}
 .radarwrap{display:grid;grid-template-columns:minmax(0,1fr);gap:18px;max-width:min(100%,900px);margin-inline:auto}#radar{display:block;width:100%;height:auto;max-height:none;background:transparent;overflow:visible}
.band{stroke:var(--line);stroke-width:1}.b0{fill:var(--band0)}.b1{fill:var(--band1)}.b2{fill:var(--band2)}.b3{fill:var(--band3)}.axis{stroke:var(--line)}
.ringlbl{font:600 10px system-ui;fill:var(--mute);letter-spacing:.12em}.qlbl{font:700 17px system-ui}.qlbl.q0,.num.q0,.qh.q0{color:var(--q0);fill:var(--q0)}.qlbl.q1,.num.q1,.qh.q1{color:var(--q1);fill:var(--q1)}.qlbl.q2,.num.q2,.qh.q2{color:var(--q2);fill:var(--q2)}.qlbl.q3,.num.q3,.qh.q3{color:var(--q3);fill:var(--q3)}
 .qlbl{font:700 16px/1.2 system-ui;paint-order:stroke;stroke:var(--bg);stroke-width:5px;stroke-linejoin:round}.blip{cursor:pointer;transition:opacity .18s ease,filter .18s ease}.blip .hit{fill:transparent;pointer-events:all}.blip .marker{transition:transform .18s ease;transform-box:fill-box;transform-origin:center}.blip .sh{stroke:var(--bg);stroke-width:2}.blip.q0 .sh{fill:var(--q0)}.blip.q1 .sh{fill:var(--q1)}.blip.q2 .sh{fill:var(--q2)}.blip.q3 .sh{fill:var(--q3)}.blip text{font:700 11px system-ui;fill:var(--bi);text-anchor:middle;pointer-events:none}
 .blip:hover .marker,.blip:focus .marker,.blip.hl .marker{transform:scale(1.16)}.blip:hover .sh,.blip:focus .sh,.blip.hl .sh{stroke:var(--ink);stroke-width:3}.hide{display:none!important}
.legend{display:flex;gap:18px;flex-wrap:wrap;font:14px system-ui;color:var(--mute);align-items:center}.legend svg{vertical-align:middle;margin-right:6px}
.ringcards{list-style:none;padding:0;margin:20px 0;display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}.ringcard{border:1px solid var(--line);background:var(--card);border-radius:14px;padding:16px}.ringcard h3{margin:0 0 6px;font-size:18px}.ringcard p{margin:.2em 0 .6em;font-size:15px}.ringcard ul{margin:0;padding-left:18px;font-size:14px;color:var(--mute)}.count{font:600 12px system-ui;color:var(--mute);border:1px solid var(--line);border-radius:99px;padding:1px 8px;margin-left:4px}
.theme{max-width:72ch;margin:34px 0}.theme h3{font-size:24px;margin:0 0 .4em}.bliplink{text-decoration-thickness:1px;text-underline-offset:3px}.chips{display:flex;gap:6px;flex-wrap:wrap}.chip{font:500 13px system-ui;border:1px solid var(--line);border-radius:99px;padding:3px 10px;text-decoration:none;color:var(--ink);background:var(--card)}
.qh{font-size:24px;margin:34px 0 4px}.rh{font:700 13px system-ui;letter-spacing:.14em;text-transform:uppercase;color:var(--mute);margin:22px 0 10px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px}
.card{border:1px solid var(--line);background:var(--card);border-radius:14px;padding:16px 18px;scroll-margin-top:80px}.card:target{outline:3px solid var(--accent)}.card h5{font-size:17px;margin:0 0 6px;display:flex;gap:8px;align-items:center}
.num{display:inline-grid;place-items:center;min-width:26px;height:26px;border-radius:99px;border:2px solid currentColor;font:700 12px system-ui}.tags{margin:0 0 8px}.tag{font-size:12px;border:1px solid var(--line);border-radius:6px;padding:1px 7px;margin-right:6px;color:var(--mute)}.tag.st{color:var(--accent);border-color:var(--accent)}
.desc{font-size:15px}.desc p{margin:.3em 0}.meta{font-size:12.5px;color:var(--mute);margin:10px 0 0}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:15px}th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line)}th{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--mute)}
ol.keep{max-width:68ch;padding-left:22px}details{border-bottom:1px solid var(--line);max-width:74ch}summary{cursor:pointer;padding:14px 0;font-weight:600;font-size:16px}details p{margin:0 0 16px}
footer{padding:36px 0 60px;color:var(--mute);font:14px/1.6 system-ui}footer a{color:inherit}
:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
.theme-settings{max-width:none;margin-top:20px;padding:0 16px 16px;border:1px solid var(--line);border-radius:12px;background:var(--card)}.theme-settings summary{color:var(--accent)}.palette{display:flex;flex-wrap:wrap;gap:14px 22px}.palette label{display:flex;align-items:center;gap:8px}.palette select,.palette input{background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:6px;min-height:36px;font:inherit}.palette input{width:44px;cursor:pointer}.theme-settings p{font-size:14px;color:var(--mute)}
 @media(max-width:540px){.grid{grid-template-columns:minmax(0,1fr)}nav.top .in{gap:14px;padding-inline:14px}#radar{min-height:320px}.ringlbl{font-size:9px}}
 @media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}
@media print{nav.top,.tools,.btns,.skip,#radarctl,.theme-settings{display:none!important}:root[data-theme]{color-scheme:light;--bg:#fff;--ink:#171717;--mute:#525252;--line:#d4d4d4;--card:#fff;--soft:#f5f6f4;--shade:#000;--bi:#fff}body{background:#fff;color:#000;font-size:12pt}section{padding:18pt 0;break-inside:auto}.card{break-inside:avoid}details{display:block}details>*{display:block}#radar{max-height:none}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
</style></head><body>
<a class="skip" href="#radar-sec">Skip to the radar</a>
<nav class="top" aria-label="Radar"><div class="in"><strong class="ui">%%ORG%%</strong><a href="#radar-sec">Radar</a><a href="#how">How to read</a>%%CHANGESNAV%%<a href="#themes">Themes</a><a href="#blips">Blips</a><a href="#actions">Actions</a><a href="#faq">FAQ</a><a href="#about">About</a><a hidden id="open-theme" href="#theme-settings">Theme</a></div></nav>
<header class="hero"><div class="in"><div class="eyebrow">%%EDITION%% · %%PUBLISHED%%</div><h1>%%TITLE%%</h1><p class="tag-line">%%TAGLINE%%</p><p class="intro">%%INTRO%%</p>
<div class="stats">%%STATS%%<div class="stat"><b>%%NEW%%</b><span>New</span></div><div class="stat"><b>%%MOVED%%</b><span>Moved</span></div></div>
<div class="btns"><a class="btn pri" href="#radar-sec">Explore the radar</a><a class="btn" href="%%CSV%%" download="radar.csv">Download CSV</a><a class="btn" href="%%JSON%%" download="radar.json">Download JSON</a><button class="btn" id="print" type="button">Print or save as PDF</button></div></div></header>
<main>
<details class="theme-settings" id="theme-settings" hidden>
<summary>Customise Radar Theme</summary>
<p>Preview your brand colours and choose a light or dark appearance. For readability, colours are adjusted against the background. Nothing is saved until you download a copy.</p>
<div class="palette" id="palette">
<label>Appearance <select name="mode" id="theme-mode" autocomplete="off"><option value="system">Device setting</option><option value="light">Light</option><option value="dark">Dark</option></select></label>
</div>
<div class="btns"><button type="button" id="save-theme-html">Download Branded HTML</button><button type="button" id="save-theme-json">Download Theme Settings</button><button type="button" id="reset-theme">Reset Preview</button></div>
<p id="theme-status" role="status"></p>
</details>
<section id="radar-sec"><h2>The radar</h2><p class="lede">Each blip is one tool or practice. Rings show our recommendation; quadrants are topic areas. Select a blip to jump to its write-up.</p>
 <div id="radarctl" class="tools" role="toolbar" aria-label="Filter the radar">%%TABS%%<span aria-hidden="true">|</span>%%RCHIPS%%<input id="q" type="search" placeholder="Search blips" aria-label="Search blips"></div>
<div class="radarwrap">%%SVG%%</div>
<p class="legend" aria-label="Legend"><span><svg width="16" height="16"><path d="M8 1L15 14H1Z" fill="currentColor"/></svg>New</span><span><svg width="16" height="16"><path d="M8 1L15 8L8 15L1 8Z" fill="currentColor"/></svg>Moved ring</span><span><svg width="16" height="16"><circle cx="8" cy="8" r="7" fill="currentColor"/></svg>No change</span><span id="shown" class="ui"></span></p></section>
<section id="how"><h2>How to read this radar</h2><p class="lede">%%TOTAL%% blips across four quadrants. The rings run from the centre outwards.</p><ul class="ringcards">%%RINGCARDS%%</ul>
<h3 class="ui" style="font-size:19px">Keeping up without being overwhelmed</h3><ol class="keep">%%KEEP%%</ol></section>
%%CHANGES%%
%%THEMES%%
<section id="blips"><h2>All blips, in one place</h2><p class="lede">Grouped by quadrant, then ring, in the same order as the radar numbers.</p>%%CARDS%%</section>
%%ACTIONS%%
<section id="faq"><h2>FAQ</h2>%%FAQ%%</section>
<section id="about"><h2>About this radar</h2><h3 class="ui" style="font-size:18px">Contributors</h3>%%CONTRIB%%
%%ARCHIVE%%
<p>Data: <a href="%%CSV%%" download="radar.csv">radar.csv</a> and <a href="%%JSON%%" download="radar.json">radar.json</a> load into <a href="https://www.thoughtworks.com/radar/byor" rel="noopener">Thoughtworks Build Your Own Radar</a>. Next review: %%NEXTREVIEW%%.</p></section>
</main>
<footer><div class="in">Generated %%ISO%% with %%CREDIT%%. The radar method (blips, quadrants, rings, themes) is adapted from the <a href="https://www.thoughtworks.com/radar/faq" rel="noopener">Thoughtworks Technology Radar</a>; this page is independent and not affiliated with or endorsed by Thoughtworks. This is an opinion based on our own experience, not a recommendation to buy anything.</div></footer>
<script>
 (()=>{const $=s=>[...document.querySelectorAll(s)],svg=document.getElementById('radar'),VB=[[400,0,400,400],[0,0,400,400],[0,400,400,400],[400,400,400,400]];
let view='all',rings=new Set($('.chip.tog').map(c=>c.dataset.ring)),term='';
const apply=()=>{let n=0;$('.blip,.card').forEach(e=>{const ok=(view==='all'||e.dataset.q===String(view))&&rings.has(e.dataset.ring)&&e.dataset.name.includes(term);e.classList.toggle('hide',!ok);if(ok&&e.classList.contains('blip'))n++});
$('.qsec').forEach(s=>s.classList.toggle('hide',view!=='all'&&s.dataset.q!==String(view)));
svg.setAttribute('viewBox',view==='all'?'0 0 800 800':VB[view].join(' '));const s=document.getElementById('shown');if(s)s.textContent=n+' blips shown'};
 $('.tab').forEach(b=>{b.setAttribute('aria-pressed',String(b.classList.contains('on')));b.onclick=()=>{view=b.dataset.view;$('.tab').forEach(x=>{x.classList.toggle('on',x===b);x.setAttribute('aria-pressed',String(x===b))});apply()}});
 $('.chip.tog').forEach(b=>{b.setAttribute('aria-pressed','true');b.title='Show or hide '+b.textContent.trim()+' blips';b.onclick=()=>{const r=b.dataset.r;rings.has(r)?rings.delete(r):rings.add(r);b.classList.toggle('on');b.setAttribute('aria-pressed',String(rings.has(r)));apply()}});
document.getElementById('q').oninput=e=>{term=e.target.value.toLowerCase().trim();apply()};
 $('.blip').forEach(b=>{const id=b.getAttribute('href'),card=document.querySelector(id);b.onmouseenter=()=>card?.classList.add('hl');b.onmouseleave=()=>card?.classList.remove('hl');b.onfocus=()=>card?.classList.add('hl');b.onblur=()=>card?.classList.remove('hl')});
document.getElementById('print').onclick=()=>print();
const root=document.documentElement, id=s=>document.getElementById(s);
// Save the unmodified markup so downloads don't inherit temporary filters or editor controls.
const original=root.cloneNode(true), settings=id('theme-settings'), mode=id('theme-mode');
const keys=['accent','q0','q1','q2','q3'], initial={mode:root.dataset.theme};
const labels=['Accent',...$('.qh').map(h=>h.textContent.trim())];
const inputs=keys.map((key,i)=>{
  initial[key]=root.style.getPropertyValue('--brand-'+key).trim();
  const label=document.createElement('label'), input=document.createElement('input');
  label.textContent=labels[i]||'Quadrant '+i;
  input.type='color';input.name=key;input.setAttribute('autocomplete','off');
  label.append(input);id('palette').append(label);return input;
});
const config=()=>({mode:mode.value,...Object.fromEntries(keys.map((k,i)=>[k,inputs[i].value]))});
function paint(node,theme){node.dataset.theme=theme.mode;keys.forEach(k=>node.style.setProperty('--brand-'+k,theme[k]));}
function reset(){mode.value=initial.mode;inputs.forEach((input,i)=>input.value=initial[keys[i]]);paint(root,initial);}
function download(content,type,filename){
  const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');
  a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  id('theme-status').textContent='Download started: '+filename;
}
reset();settings.hidden=false;
id('open-theme').hidden=false;
id('open-theme').onclick=()=>{settings.open=true;};
id('palette').oninput=()=>{paint(root,config());id('theme-status').textContent='';};
id('reset-theme').onclick=()=>{reset();id('theme-status').textContent='Original theme restored.';};
id('save-theme-json').onclick=()=>download(JSON.stringify(config(),null,2)+'\n','application/json','radar-theme.json');
id('save-theme-html').onclick=()=>{paint(original,config());download('<!doctype html>\n'+original.outerHTML,'text/html;charset=utf-8','radar-branded.html');};
if(innerWidth<640){const t=$('.tab')[1];t&&t.click()}apply()})();
</script></body></html>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("state"); ap.add_argument("--out"); ap.add_argument("--accent"); ap.add_argument("--theme"); ap.add_argument("--public", action="store_true")
    a = ap.parse_args()
    state = json.load(open(a.state, encoding="utf-8"))
    if not state.get("blips"): sys.exit("No blips in the state yet: finish at least one domain interview (Phase 5) before building the site.")
    names = [b["name"].strip().lower() for b in state["blips"]]
    dups = sorted({n for n in names if names.count(n) > 1})
    if dups: sys.exit("Duplicate blip names (BYOR and the site need unique names): " + ", ".join(dups) + ". Rename one, for example 'Microsoft Teams (chat)' and 'Microsoft Teams (phone)'.")
    cid = state["meta"].get("edition") or CE.edition_id(); state["meta"]["edition"] = cid
    pid, pp = CE.find_previous(a.state, cid); changes = snaps = archive = None
    edir = os.path.join(os.path.dirname(os.path.abspath(a.state)), "editions")
    if pp:
        prev = json.load(open(pp, encoding="utf-8")); prev["meta"].setdefault("edition", pid); changes = CE.compare(prev, state)
        snaps = {k: v for k, v in CE.load_all(edir).items() if k != cid}
        try: archive = json.load(open(os.path.join(edir, "index.json"), encoding="utf-8"))["editions"]
        except (OSError, ValueError, KeyError): archive = None
    try:
        theme = json.load(open(a.theme, encoding="utf-8")) if a.theme else {}
        if theme is None:
            raise ValueError("Theme must be a JSON object, not null.")
        theme = theme_config(theme, a.accent)
    except (OSError, ValueError) as error:
        ap.error(str(error))
    out, warns = build(state, None, a.public, changes, snaps, archive, theme)
    path = a.out or os.path.join(os.path.dirname(os.path.abspath(a.state)), "radar-output", "index.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8", newline="\n").write(out)
    print(f"Wrote {path} ({len(out)//1024} KB, {len(state['blips'])} blips)")
    for w in warns: print("WARNING", w)


if __name__ == "__main__":
    main()
