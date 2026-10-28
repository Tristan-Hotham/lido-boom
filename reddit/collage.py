"""r/dataisbeautiful collage for The Lido Boom and Bust (lido-boom). Run from this folder: python3 collage.py
Every number is read from ../data/results.json or ../data/page_data.json."""
import json, math, os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon, Rectangle, Wedge

F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
    fm.fontManager.addfont(os.path.join(F, f))
DISP = fm.FontProperties(fname=os.path.join(F, "FrauncesVar.ttf"), weight=900)
SER = "Source Serif 4"; MONO = "IBM Plex Mono"
BG = "#F5EFE2"; FG = "#14304A"; MUT = "#5D6D77"; LAND = "#DDEBEE"; LANDE = "#A9C3CA"
POOL = "#1E8FAA"; POOLL = "#8FCAD8"; GOLD = "#C98F1E"; CORAL = "#E0603F"; UNK = "#9AA6AC"; RULE = "#D9D3C4"
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
ROWS = [dict(zip(P["cols"], r)) for r in P["rows"]]
K = math.cos(math.radians(54))
LANDP = []
for g in json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0]); LANDP.append(np.c_[a[:, 0] * K, a[:, 1]])
pct = lambda v: f"{v * 100:.0f}%"
o, c, rp, cb, cv = R["openings"], R["closures"], R["reopenings"], R["combined"], R["curve"]

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
# art-deco sunburst behind the title
bg = fig.add_axes([0.66, 0.875, 0.34, 0.125]); bg.axis("off"); bg.set_xlim(0, 1); bg.set_ylim(0, 1)
for i in range(24):
    a = math.pi * (i + .5) / 24
    bg.plot([0.55 + math.cos(a) * .16, 0.55 + math.cos(a) * .48], [0.02 + math.sin(a) * .26, 0.02 + math.sin(a) * .8], color=GOLD, lw=2.4, alpha=.35, solid_capstyle="butt")
bg.add_patch(Wedge((0.55, 0.02), 0.13, 0, 180, color=GOLD, alpha=.55, transform=bg.transData)); bg.set_aspect("auto")
fig.text(0.04, 0.968, "Whatever happened to\nBritain's lidos?", fontproperties=DISP, fontsize=44, color=FG, va="top", linespacing=.98)
fig.text(0.04, 0.874, f"An open register of {R['register']['n']} lidos and open-air pools, each followed from opening day to today,\n"
         f"plus every working outdoor pool in OpenStreetMap. A boom, a bust, and a stubborn comeback.",
         family=SER, fontsize=14.5, color=FG, va="top", linespacing=1.4)

# hero map
ax = fig.add_axes([0.0, 0.355, 0.6, 0.45])
for a in LANDP:
    ax.add_patch(Polygon(a, closed=True, fc=LAND, ec=LANDE, lw=.6, zorder=0))
ax.set_xlim(-7.4 * K, 1.95 * K); ax.set_ylim(49.85, 58.75); ax.set_aspect("equal"); ax.axis("off")


def st(r):
    if r["layer"] == "osm": return "osm" if r["status"] == "open" else "shut"
    if r["status"] == "open": return "back" if r["reopened"] else "open"
    return "unk" if r["status"] == "unknown" else "shut"


for k, col, s, z in [("osm", POOL, 22, 1), ("unk", UNK, 70, 2), ("shut", CORAL, 95, 3), ("open", POOL, 95, 4), ("back", GOLD, 120, 5)]:
    v = [r for r in ROWS if st(r) == k]
    if k == "osm":
        ax.scatter([r["lon"] * K for r in v], [r["lat"] for r in v], s=s, c=col, alpha=.75, lw=0, zorder=z)
    else:
        ax.scatter([r["lon"] * K for r in v], [r["lat"] for r in v], s=s * 2.4, c=col, alpha=.18, lw=0, zorder=z)
        ax.scatter([r["lon"] * K for r in v], [r["lat"] for r in v], s=s, c=col, edgecolors=FG, lw=.6, zorder=z + .5,
                   marker="D" if k == "back" else "s" if k == "shut" else "o")
lab = {r["id"]: r for r in ROWS}
for i_, txt, dx, dy, ha in [("jubilee", "Jubilee Pool, Penzance\n1935", -8, -16, "left"), ("thames", "Thames Lido, Reading\nshut 1974 to 2017", -70, 40, "right"),
                            ("grange", "Grange Lido\nclosed 1993", -14, 6, "right"), ("newbrighton", "New Brighton\nlargest lido in Britain, 1934", -14, 2, "right"),
                            ("tooting", "Tooting Bec, 1906", 70, -36, "left")]:
    r = lab[i_]
    ax.annotate(txt, (r["lon"] * K, r["lat"]), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", family=MONO, fontsize=10, color=FG, zorder=8,
                bbox=dict(fc=BG, ec="none", alpha=.85, pad=1.2), arrowprops=dict(arrowstyle="-", color=FG, lw=.7) if i_ in ("tooting", "thames") else None)
key = [(POOL, "o", "open"), (GOLD, "D", "closed, then reopened"), (CORAL, "s", "closed"), (UNK, "o", "unknown"), (POOL, ".", "OpenStreetMap only")]
xs = [0.04, 0.125, 0.335, 0.425, 0.53]
for (col, m, t), x0 in zip(key, xs):
    kx = fig.add_axes([x0, 0.802, 0.012, 0.0096]); kx.axis("off"); kx.set_xlim(-1, 1); kx.set_ylim(-1, 1)
    kx.scatter([0], [0], s=60 if m != "." else 18, c=col, marker=m if m != "." else "o", edgecolors=FG if m != "." else "none", lw=.6)
    fig.text(x0 + .015, 0.807, t, va="center", family=MONO, fontsize=10.5, color=FG)

# headline numbers
tx = fig.add_axes([0.62, 0.36, 0.36, 0.44]); tx.axis("off")
notes = [(f"{o['d1930s']} of {o['n_dated']}", POOL, f"documented lidos with an opening date\nopened in the 1930s. {o['y1935']} opened in 1935,\nthe year of George V's Silver Jubilee."),
         (f"{c['n_1970_1999']} of {c['n_dated']}", CORAL, f"dated closures came between 1970 and\n1999. The 1990s were the worst decade,\nwith {c['d1990s']}."),
         (f"{rp['n']}", GOLD, f"closed lidos have reopened, {rp['since_2000']} of them\nsince 2000, after a median {rp['median_years_shut']} years shut.\nReading's Thames Lido waited {rp['max_years_shut']}."),
         (pct(cb["share_coastal_open"]), POOL, f"of the {cb['open']} working open-air pools I can\nplace today are within 2 km of the sea.\n{pct(cb['share_south'])} are in London, the South East or\nthe South West.")]
for (big, col, small), y in zip(notes, [1.0, 0.75, 0.50, 0.25]):
    tx.text(0, y, big, fontproperties=DISP, fontsize=38, color=col, va="top", transform=tx.transAxes)
    tx.text(0, y - 0.085, small, family=SER, fontsize=12.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)

# small multiple 1: documented lidos in use
fig.text(0.04, 0.33, "DOCUMENTED LIDOS OPEN (BLUE) AND SHUT (CORAL), 1900 TO 2026", family=MONO, fontsize=10.5, color=MUT)
bx = fig.add_axes([0.06, 0.14, 0.5, 0.175], facecolor=BG)
C = P["curve"]; y = [q["year"] for q in C]; op = np.array([q["open"] for q in C]); sh = np.array([q["shut"] for q in C])
bx.fill_between(y, 0, op, color=POOL, lw=0, alpha=.92)
bx.fill_between(y, op, op + sh, color=CORAL, lw=0, alpha=.8)
for yy, txt in [(cv["peak_year"], f"{cv['peak_year']}: {cv['peak_open']} open")]:
    bx.annotate(txt, (yy, cv["peak_open"]), xytext=(1928, 43), family=MONO, fontsize=10, color=FG, arrowprops=dict(arrowstyle="-", color=FG, lw=.7))
bx.text(cv["low_year"], cv["low_open"] / 2, f"{cv['low_year']}:\n{cv['low_open']} open", family=MONO, fontsize=10, color="white", ha="center", va="center")
bx.set_xlim(1900, 2026); bx.set_ylim(0, 48)
for sp in ("top", "right"): bx.spines[sp].set_visible(False)
bx.spines["left"].set_color(MUT); bx.spines["bottom"].set_color(MUT)
bx.tick_params(labelsize=10, colors=FG); [t.set_family(MONO) for t in bx.get_xticklabels() + bx.get_yticklabels()]
bx.grid(axis="y", color=RULE, lw=.8); bx.set_axisbelow(True)

# small multiple 2: the comebacks
fig.text(0.63, 0.33, "CLOSED (CORAL) TO REOPENED (GOLD)", family=MONO, fontsize=10.5, color=MUT)
dx = fig.add_axes([0.80, 0.14, 0.18, 0.175], facecolor=BG)
V = [d for d in rp["list"] if d["closed"]]
for i, d in enumerate(V):
    yy = len(V) - i
    dx.plot([d["closed"], d["reopened"]], [yy, yy], color=MUT, lw=1.3)
    dx.scatter([d["closed"]], [yy], s=22, color=CORAL, marker="s", zorder=3)
    dx.scatter([d["reopened"]], [yy], s=26, color=GOLD, marker="D", edgecolors=FG, lw=.4, zorder=3)
    fig.text(0.795, 0.14 + 0.175 * (yy - .5) / (len(V) + .0), d["name"].split(" (")[0], family=MONO, fontsize=9.2, color=FG, ha="right", va="center")
dx.set_ylim(.5, len(V) + .5); dx.set_xlim(1970, 2026); dx.set_yticks([])
dx.set_xticks([1980, 2000, 2020])
for sp in ("top", "right", "left"): dx.spines[sp].set_visible(False)
dx.spines["bottom"].set_color(MUT); dx.tick_params(labelsize=10, colors=FG); [t.set_family(MONO) for t in dx.get_xticklabels()]
dx.grid(axis="x", color=RULE, lw=.8); dx.set_axisbelow(True)

fig.text(0.04, 0.083, "A documented sample, not a census: survivors are better recorded than pools that quietly closed, so the real decline was steeper.\n"
         f"Wikipedia says 169 lidos were built in the 1930s; my register holds {R['thirties']['n']} of them. Today's map is a floor, not a count.",
         family=MONO, fontsize=9.5, color=MUT, linespacing=1.45)
fig.text(0.04, 0.012,
         "Data: English Wikipedia articles on lidos, towns and parks (CC BY-SA 4.0); Wikidata (CC0); OpenStreetMap, © OpenStreetMap contributors (ODbL), via QLever;\n"
         "OS Open Names (Contains OS data © Crown copyright and database right 2026, OGL v3); ONS Census 2021 (OGL v3); Natural Earth coastline.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib.  tristan-hotham.github.io/lido-boom",
         family=MONO, fontsize=8.8, color=MUT, linespacing=1.5)
fig.savefig(os.path.join(HERE, "whatever_happened_to_britains_lidos.png"), facecolor=BG, dpi=200)
print("ok")
