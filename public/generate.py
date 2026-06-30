import json
import re
from pathlib import Path
from html import escape
from datetime import datetime

BASE_URL = "https://dmv-cloud-hub.dmvverifyy.workers.dev"
ROOT = Path(__file__).parent
OUT = ROOT / "public"
CONTENT_DIR = ROOT / "content" / "guides"

def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:100]

def parse_front_matter(path):
    raw = path.read_text(encoding="utf-8")
    data, body = {}, raw
    if raw.startswith("---"):
        _, fm, body = raw.split("---", 2)
        for line in fm.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip().strip('"')
    return data, body.strip()

def linkify(text):
    return re.sub(r"(https?://[^\s<]+)", r'<a href="\1" target="_blank" rel="noopener">\1</a>', text)

def md_to_html(md):
    html, in_ul, in_ol = [], False, False
    for line in md.splitlines():
        s = line.strip()
        if not s:
            if in_ul:
                html.append("</ul>")
                in_ul = False
            if in_ol:
                html.append("</ol>")
                in_ol = False
            continue
        if s.startswith("## "):
            if in_ul:
                html.append("</ul>")
                in_ul = False
            if in_ol:
                html.append("</ol>")
                in_ol = False
            html.append("<h2>" + escape(s[3:]) + "</h2>")
        elif s.startswith("### "):
            html.append("<h3>" + escape(s[4:]) + "</h3>")
        elif re.match(r"^\\d+\\.\\s+", s):
            if not in_ol:
                html.append("<ol>")
                in_ol = True
            item = re.sub(r"^\\d+\\.\\s+", "", s)
            html.append("<li>" + linkify(escape(item)) + "</li>")
        elif s.startswith("- "):
            if not in_ul:
                html.append("<ul>")
                in_ul = True
            html.append("<li>" + linkify(escape(s[2:])) + "</li>")
        else:
            if in_ul:
                html.append("</ul>")
                in_ul = False
            if in_ol:
                html.append("</ol>")
                in_ol = False
            html.append("<p>" + linkify(escape(s)) + "</p>")
    if in_ul:
        html.append("</ul>")
    if in_ol:
        html.append("</ol>")
    return "\\n".join(html)

def load_guides():
    guides = []
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(CONTENT_DIR.glob("*.md")):
        fm, body = parse_front_matter(path)
        title = fm.get("title") or path.stem.replace("-", " ").title()
        slug = fm.get("slug") or slugify(title)
        state = fm.get("state", "")
        guides.append({
            "title": title,
            "slug": slug,
            "state": state,
            "state_slug": slugify(state) if state else "",
            "type": fm.get("type", "guide"),
            "description": fm.get("description", title),
            "body": body,
            "path": "/guides/" + slug + "/"
        })
    return guides

def render_guide(g):
    canonical = BASE_URL + g["path"]
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(g["title"])}</title><meta name="description" content="{escape(g["description"])}"><link rel="canonical" href="{canonical}"><link rel="stylesheet" href="/assets/css/style.css"></head><body><main class="page"><div class="crumb">DMV Hub / Guide</div><h1>{escape(g["title"])}</h1><p class="meta">{escape(g["description"])}</p><article class="card article-body">{md_to_html(g["body"])}</article><section class="card"><strong>Related:</strong><br><a href="/state/{g["state_slug"]}/">{escape(g["state"])} DMV guide index</a></section><div class="footer">Unofficial guide. Always verify requirements with your official state DMV.</div></main></body></html>'''

def render_state_page(item, all_states, guides):
    state = escape(item["state"])
    slug = item["slug"]
    official_url = escape(item["official_url"])
    official_name = escape(item["official_name"])
    dmvverify_url = escape(item["dmvverify_url"])
    state_guides = [g for g in guides if g["state_slug"] == slug]
    cards = ""
    for g in state_guides:
        cards += f'<a class="link-row" href="{g["path"]}"><div class="link-icon wp">&#128196;</div><div class="link-text"><div class="link-title">{escape(g["title"])}</div><div class="link-desc">{escape(g["description"])}</div></div><span class="hub-badge">Guide</span></a>'
    if not cards:
        cards = '<p class="muted">Guides will be added soon.</p>'
    other = "".join(f'<a class="state-pill" href="/state/{s["slug"]}/">→ {escape(s["state"])}</a>' for s in all_states if s["slug"] != slug)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{state} DMV Guide Index | DMV Hub</title><meta name="description" content="{state} driver license renewal, REAL ID, replacement, registration, and official DMV resources."><link rel="canonical" href="{BASE_URL}/state/{slug}/"><link rel="stylesheet" href="/assets/css/style.css"></head><body><main class="page"><header class="hero"><div class="crumb">DMV Hub /state/{slug}/</div><h1>{state} DMV - Complete guide index</h1><p>{state} driver license renewal, REAL ID, replacement, registration, and official DMV resources.</p></header><section class="section-card"><h2>Step-by-step guides</h2>{cards}</section><section class="section-card"><h2>Official source</h2><a class="link-row" href="{official_url}" target="_blank" rel="noopener"><div class="link-icon official">&#127963;</div><div class="link-text"><div class="link-title">{official_name}</div><div class="link-desc">Appointments, fee lookup, official forms, and state DMV information</div></div><span class="hub-badge">Official</span></a></section><section class="section-card featured"><h2>Full fee & eligibility checker</h2><a class="link-row" href="{dmvverify_url}" target="_blank" rel="noopener"><div class="link-icon dmv">&#128269;</div><div class="link-text"><div class="link-title">{state} renewal eligibility - DMVVerify</div><div class="link-desc">Check fee, eligibility, and fastest renewal path</div></div><span class="hub-badge">Tool</span></a></section><footer class="footer"><div class="footer-title">Other states</div><div class="state-grid">{other}</div></footer></main></body></html>'''

def render_home(states, guides):
    latest = "".join(f'<a class="state-card" href="{g["path"]}"><strong>{escape(g["title"])}</strong><span>{escape(g["description"])}</span></a>' for g in guides[:12])
    state_cards = "".join(f'<a class="state-card" href="/state/{s["slug"]}/"><strong>{escape(s["state"])}</strong><span>{escape(s.get("description","DMV resources"))}</span></a>' for s in states)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DMV Hub | State DMV Guides</title><meta name="description" content="State DMV guide index for renewals, REAL ID, replacements, fees, and official DMV resources."><link rel="canonical" href="{BASE_URL}/"><link rel="stylesheet" href="/assets/css/style.css"></head><body><main class="page"><header class="hero"><div class="crumb">DMV Hub</div><h1>State-by-State DMV Guide Index</h1><p>Find DMV renewal, REAL ID, replacement, fee, and official source guides.</p></header><h2>Latest guides</h2><section class="state-list">{latest or '<p>No guides yet.</p>'}</section><h2>All states</h2><section class="state-list">{state_cards}</section></main></body></html>'''

def generate_sitemap(states, guides):
    urls = [BASE_URL + "/"] + [BASE_URL + "/state/" + s["slug"] + "/" for s in states] + [BASE_URL + g["path"] for g in guides]
    today = datetime.utcnow().date()
    return '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls) + "</urlset>"

def main():
    states = json.loads((ROOT / "states_data.json").read_text(encoding="utf-8"))
    guides = load_guides()
    (OUT / "assets/css").mkdir(parents=True, exist_ok=True)
    (OUT / "state").mkdir(parents=True, exist_ok=True)
    (OUT / "guides").mkdir(parents=True, exist_ok=True)
    (OUT / "assets/css/style.css").write_text((ROOT / "assets/css/style.css").read_text(encoding="utf-8"), encoding="utf-8")
    (OUT / "index.html").write_text(render_home(states, guides), encoding="utf-8")
    for s in states:
        d = OUT / "state" / s["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render_state_page(s, states, guides), encoding="utf-8")
    for g in guides:
        d = OUT / "guides" / g["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render_guide(g), encoding="utf-8")
    (OUT / "sitemap.xml").write_text(generate_sitemap(states, guides), encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\\nAllow: /\\nSitemap: " + BASE_URL + "/sitemap.xml\\n", encoding="utf-8")
    print(f"Generated {len(states)} states and {len(guides)} guides")

if __name__ == "__main__":
    main()
