import json
from pathlib import Path
from html import escape
from datetime import datetime

BASE_URL = "https://dmv-cloud-hub.localmapdominanceseo.workers.dev"
ROOT = Path(__file__).parent
OUT = ROOT / "public"
STATE_DIR = OUT / "state"

def guide_title(kind, state):
    return {
        "renewal": f"How to renew your {state} driver's license",
        "real_id": f"{state} REAL ID — what you need and how to apply",
        "lost_license": f"Lost or stolen {state} license — replacement steps",
        "registration": f"{state} vehicle registration renewal guide",
    }.get(kind, f"{state} DMV guide")

def guide_desc(kind):
    return {
        "renewal": "Online, by mail, and in-person — fees, eligibility, and timeline",
        "real_id": "Documents checklist, DMV appointment, and upgrade process",
        "lost_license": "Replacement steps, fees, and temporary license info",
        "registration": "Requirements, fees, and online renewal options",
    }.get(kind, "Step-by-step DMV resource")

def render_state_page(item, all_states):
    state = escape(item["state"])
    slug = item["slug"]
    desc = escape(item.get("description", ""))
    rows = []
    for kind, url in item.get("wordpress_guides", {}).items():
        if not url:
            continue
        icon = {"renewal":"📄", "real_id":"🪪", "lost_license":"⚠️", "registration":"🚗"}.get(kind, "📘")
        rows.append(f'''
        <a class="link-row" href="{escape(url)}" target="_blank" rel="noopener">
          <div class="link-icon wp">{icon}</div>
          <div class="link-text"><div class="link-title">{guide_title(kind, state)}</div><div class="link-desc">{guide_desc(kind)}</div></div>
          <span class="hub-badge wp">Guide</span>
        </a>''')
    guide_html = "\n".join(rows) if rows else '<p class="muted">Guides will be added soon.</p>'
    other = "".join(f'<a class="state-pill" href="/state/{s["slug"]}/">→ {escape(s["state"])}</a>' for s in all_states if s["slug"] != slug)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{state} DMV Guide Index | DMV Hub</title><meta name="description" content="{desc}">
<link rel="canonical" href="{BASE_URL}/state/{slug}/"><link rel="stylesheet" href="/assets/css/style.css"></head>
<body><main class="page"><header class="hero"><div class="crumb">DMV Hub /state/{slug}/</div><h1>{state} DMV — Complete guide index</h1><p>{desc}</p></header>
<section class="section-card"><h2>Step-by-step guides</h2>{guide_html}</section>
<section class="section-card"><h2>Official source</h2><a class="link-row" href="{escape(item['official_url'])}" target="_blank" rel="noopener"><div class="link-icon official">🏛️</div><div class="link-text"><div class="link-title">{escape(item['official_name'])}</div><div class="link-desc">Appointments, fee lookup, official forms, and state DMV information</div></div><span class="hub-badge official">Official</span></a></section>
<section class="section-card featured"><h2>Full fee & eligibility checker</h2><a class="link-row" href="{escape(item['dmvverify_url'])}" target="_blank" rel="noopener"><div class="link-icon dmv">🔎</div><div class="link-text"><div class="link-title">{state} renewal eligibility — DMVVerify</div><div class="link-desc">Check fee, eligibility, and the fastest renewal path</div></div><span class="hub-badge dmv">Tool</span></a></section>
<footer class="footer"><div class="footer-title">Other states</div><div class="state-grid">{other}</div></footer></main></body></html>'''

def render_home(data):
    cards = "".join(f'<a class="state-card" href="/state/{s["slug"]}/"><strong>{escape(s["state"])}</strong><span>{escape(s.get("description", "DMV resources"))}</span></a>' for s in data)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DMV Hub | State-by-State DMV Guide Index</title><meta name="description" content="State-by-state DMV guide index."><link rel="canonical" href="{BASE_URL}/"><link rel="stylesheet" href="/assets/css/style.css"></head><body><main class="page"><header class="hero"><div class="crumb">DMV Hub</div><h1>State-by-State DMV Guide Index</h1><p>Find driver license renewal, REAL ID, replacement, and official DMV resources by state.</p></header><section class="state-list">{cards}</section></main></body></html>'''

def sitemap(data):
    today = datetime.utcnow().date()
    urls = [f"{BASE_URL}/"] + [f"{BASE_URL}/state/{s['slug']}/" for s in data]
    return '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{u}</loc><lastmod>{today}</lastmod></url>' for u in urls) + '</urlset>'

def main():
    data = json.loads((ROOT / "states_data.json").read_text(encoding="utf-8"))
    (OUT / "assets/css").mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (OUT / "assets/css/style.css").write_text((ROOT / "assets/css/style.css").read_text(encoding="utf-8"), encoding="utf-8")
    (OUT / "index.html").write_text(render_home(data), encoding="utf-8")
    for item in data:
        d = STATE_DIR / item["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render_state_page(item, data), encoding="utf-8")
    (OUT / "sitemap.xml").write_text(sitemap(data), encoding="utf-8")
    print(f"Generated {len(data)} state pages in {OUT}")

if __name__ == "__main__":
    main()
