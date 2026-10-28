"""Step 5. Render ../header.png (1200x630 social card) with Playwright Chromium.

Fonts: pass a folder holding FrauncesVar.ttf, SourceSerif4-Regular.ttf, IBMPlexMono-Regular.ttf and
IBMPlexMono-Medium.ttf as FONT_DIR (from github.com/google/fonts); otherwise system serif is used.
Coastline: Natural Earth 1:10m land for the British Isles, as extracted for the lighthouse project.
Dots: register entries (big) and OpenStreetMap-only sites (small), coloured by status today.
Run: FONT_DIR=/path/to/fonts python3 05_header.py
"""
import json, math, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
FD = os.environ.get("FONT_DIR", "")
K = math.cos(math.radians(52.5))
X0, X1, Y0, Y1 = -7.6 * K, 1.9 * K, -58.8, -49.9
Hh = 610; Ww = Hh * (X1 - X0) / (Y1 - Y0)


def pr(lat, lon):
    return (lon * K - X0) / (Y1 - Y0) * Hh, (-lat - Y0) / (Y1 - Y0) * Hh


COAST = os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json")
land = ""
for g in json.load(open(COAST)):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        ring = poly[0]
        land += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in (pr(q[1], q[0]) for q in ring)) + "Z"
COL = {"open": "#2496B0", "back": "#C98F1E", "shut": "#E0603F", "unk": "#9AA6AC"}
dots = ""
rows = [dict(zip(P["cols"], r)) for r in P["rows"]]
def st(r):
    if r["layer"] == "osm": return "open" if r["status"] == "open" else "shut"
    if r["status"] == "open": return "back" if r["reopened"] else "open"
    return "unk" if r["status"] == "unknown" else "shut"
for r in sorted(rows, key=lambda r: r["layer"] == "register"):
    x, y = pr(r["lat"], r["lon"]); s_ = st(r); big = r["layer"] == "register"
    dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{5.2 if big else 3.2}" fill="{COL[s_]}" fill-opacity="{0.95 if big else 0.7}" stroke="#14304A" stroke-opacity="{0.5 if big else 0}" stroke-width="0.8"/>'
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:radial-gradient(circle at 78% 50%,#FBF7EE 0%,#F4EFE4 55%,#E3ECEC 100%);color:#14304A;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:66px;top:62px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#5D6D77;display:flex;gap:12px;align-items:center}}
.k b{{background:#2496B0;color:#F4EFE4;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:60px;top:100px;margin:0;font:900 92px/.92 Fraunces,Georgia,serif;letter-spacing:-.02em;color:#14304A;width:660px}}
h1 em{{font-style:normal;color:#2496B0}} h1 i{{font-style:normal;color:#E0603F}}
p{{position:absolute;left:66px;top:318px;width:600px;margin:0;font-size:26px;line-height:1.36}}
p b{{color:#2496B0}} p b.c{{color:#E0603F}} p b.g{{color:#C98F1E}}
.f{{position:absolute;left:66px;bottom:40px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#5D6D77}}
svg{{position:absolute;right:26px;top:10px}}
</style></head><body>
<div class="k"><b>Data study</b><span>Open-air pools · Britain · 1815 to 2026</span></div>
<h1>The lido <em>boom</em> and <i>bust</i></h1>
<p><b>{R['openings']['d1930s']}</b> of {R['openings']['n_dated']} dated openings came in the 1930s. <b class="c">{R['closures']['n_1970_1999']}</b> of {R['closures']['n_dated']} dated closures came in 1970 to 1999. Then <b class="g">{R['reopenings']['n']}</b> came back.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{Ww:.0f}" height="{Hh}" viewBox="0 0 {Ww:.0f} {Hh}"><path d="{land}" fill="#DCE8EA" stroke="#B8C7CB" stroke-width="1"/>{dots}</svg>
</body></html>"""
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
tmp = os.path.join(ROOT, "work", "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")
