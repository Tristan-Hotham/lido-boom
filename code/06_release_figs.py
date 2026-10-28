"""Step 6. Static figures for the paper (release/paper/f_*.png) and the blog (release/blog/b_*.png), from ../data.
Fonts: FONT_DIR as in 05_header.py (Fraunces, Source Serif 4, IBM Plex Mono); otherwise matplotlib defaults.
Run: FONT_DIR=/path/to/fonts python3 06_release_figs.py
"""
import json, math, os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
ROWS = [dict(zip(P["cols"], r)) for r in P["rows"]]
FD = os.environ.get("FONT_DIR", "")
MONO, SER = "DejaVu Sans Mono", "DejaVu Serif"
if FD and os.path.exists(os.path.join(FD, "IBMPlexMono-Regular.ttf")):
    for f in ["IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
        fm.fontManager.addfont(os.path.join(FD, f))
    MONO, SER = "IBM Plex Mono", "Source Serif 4"
BG, FG, MUT, RULE, LAND, LANDE = "#FFFFFF", "#14304A", "#5D6D77", "#D5DDDF", "#E6EEEF", "#B8C7CB"
POOL, POOLL, GOLD, CORAL, UNK = "#2496B0", "#9FD3DF", "#C98F1E", "#E0603F", "#9AA6AC"
K = math.cos(math.radians(54))
LANDP = []
for g in json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0]); LANDP.append(np.c_[a[:, 0] * K, a[:, 1]])
PAP = os.path.join(ROOT, "release", "paper"); BLOG = os.path.join(ROOT, "release", "blog")
os.makedirs(PAP, exist_ok=True); os.makedirs(BLOG, exist_ok=True)
plt.rcParams.update({"font.family": MONO, "axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": FG, "ytick.color": FG})


def style(ax, grid="y"):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    if grid: ax.grid(axis=grid, color=RULE, lw=.8); ax.set_axisbelow(True)


def save(fig, name, blog):
    if blog:
        fig.savefig(os.path.join(BLOG, "b_" + name + ".png"), dpi=200, facecolor=BG)
    else:
        fig.savefig(os.path.join(PAP, "f_" + name + ".png"), dpi=220, facecolor=BG)
    plt.close(fig)


def status(r):
    if r["layer"] == "osm": return "osm" if r["status"] == "open" else "shut"
    if r["status"] == "open": return "back" if r["reopened"] else "open"
    return "unk" if r["status"] == "unknown" else "shut"


SC = {"open": (POOL, "o"), "back": (GOLD, "D"), "shut": (CORAL, "s"), "unk": (UNK, "^"), "osm": (POOL, ".")}
LAB = {"open": "Open, no long closure on record", "back": "Reopened, open today", "shut": "Closed now", "unk": "Status unknown", "osm": "Working pool, OpenStreetMap only"}


def fig_map(blog):
    w = 7.6 if blog else 6.2
    fig = plt.figure(figsize=(w, w * 1.18), facecolor=BG); ax = fig.add_axes([0, 0, 1, 1])
    for a in LANDP: ax.add_patch(Polygon(a, closed=True, fc=LAND, ec=LANDE, lw=.5, zorder=0))
    for k in ["osm", "unk", "shut", "open", "back"]:
        v = [r for r in ROWS if status(r) == k]
        c, m = SC[k]
        ax.scatter([r["lon"] * K for r in v], [r["lat"] for r in v], s=(16 if k == "osm" else 34) * (1.3 if blog else 1), c=c, marker=m,
                   edgecolors=FG if k != "osm" else "none", linewidths=.5, alpha=.95, zorder=3, label=f"{LAB[k]} ({len(v)})")
    ax.set_xlim(-8.3 * K, 2.0 * K); ax.set_ylim(49.85, 59.0); ax.set_aspect("equal"); ax.axis("off")
    ax.legend(loc="upper left", frameon=False, fontsize=10 if blog else 8, bbox_to_anchor=(0.0, 0.99), handletextpad=.3, labelspacing=.5)
    save(fig, "map", blog)


def fig_decades(blog):
    D = R["decades"]; x = np.arange(len(D))
    fig, ax = plt.subplots(figsize=(7.6 if blog else 6.4, 3.9 if blog else 3.2), facecolor=BG)
    for j, (k, c, h) in enumerate([("opened", POOL, None), ("closed", CORAL, "///"), ("reopened", GOLD, "..")]):
        ax.bar(x + (j - 1) * .27, [d[k] for d in D], width=.26, color=c, hatch=h, edgecolor="white", lw=.3, label=k.capitalize())
    ax.set_xticks(x); ax.set_xticklabels([("'" + str(d["decade"])[2:]) if blog else str(d["decade"]) + "s" for d in D], fontsize=10 if blog else 7.5, rotation=0 if blog else 45)
    ax.set_ylabel("pools in the register", fontsize=10 if blog else 8)
    ax.legend(frameon=False, fontsize=10 if blog else 8)
    i = [d["decade"] for d in D].index(1930)
    ax.annotate(f"{D[i]['opened']} opened in the 1930s", (i - .27, D[i]["opened"]), xytext=(i + .6, D[i]["opened"] - 2), fontsize=10 if blog else 8, color=FG, va="top")
    style(ax); fig.tight_layout(); save(fig, "decades", blog)


def fig_curve(blog):
    C = P["curve"]; y = [c["year"] for c in C]; o = np.array([c["open"] for c in C]); s = np.array([c["shut"] for c in C])
    fig, ax = plt.subplots(figsize=(7.6 if blog else 6.4, 3.9 if blog else 3.0), facecolor=BG)
    ax.fill_between(y, 0, o, color=POOL, alpha=.9, lw=0, label="Open")
    ax.fill_between(y, o, o + s, color=CORAL, alpha=.75, lw=0, hatch="///", edgecolor="white", label="Closed (not yet reopened)")
    cv = R["curve"]
    ax.annotate(f"{cv['peak_year']}: {cv['peak_open']} open", (cv["peak_year"], cv["peak_open"]), xytext=(1935, 42), fontsize=10 if blog else 8, arrowprops=dict(arrowstyle="-", color=FG, lw=.7))
    ax.annotate(f"{cv['low_year']}: {cv['low_open']} open", (cv["low_year"], cv["low_open"]), xytext=(1984, 12), fontsize=10 if blog else 8, color="white")
    ax.set_xlim(1900, 2026); ax.set_ylim(0, 46); ax.set_ylabel("documented pools", fontsize=10 if blog else 8)
    ax.legend(frameon=False, loc="upper left", fontsize=10 if blog else 8)
    style(ax); fig.tight_layout(); save(fig, "curve", blog)


def fig_comeback(blog):
    V = R["reopenings"]["list"]
    fig, ax = plt.subplots(figsize=(7.6 if blog else 6.4, 4.8 if blog else 3.8), facecolor=BG)
    for i, d in enumerate(V):
        yy = len(V) - i
        if d["closed"]:
            ax.plot([d["closed"], d["reopened"]], [yy, yy], color=MUT, lw=1.6, zorder=1)
            ax.scatter([d["closed"]], [yy], color=CORAL, marker="s", s=40, zorder=2)
        ax.scatter([d["reopened"]], [yy], color=GOLD, marker="D", s=40, zorder=2, edgecolors=FG, linewidths=.4)
    ax.set_yticks([len(V) - i for i in range(len(V))]); ax.set_yticklabels([d["name"].split(" (")[0] for d in V], fontsize=10 if blog else 8)
    ax.set_xlim(1970, 2026)
    ax.legend(handles=[Line2D([], [], color=CORAL, marker="s", ls="", label="closed"), Line2D([], [], color=GOLD, marker="D", ls="", label="reopened")],
              frameon=False, loc="upper right", fontsize=10 if blog else 8)
    style(ax, "x"); fig.tight_layout(); save(fig, "comeback", blog)


def fig_regions(blog):
    V = R["regions"][::-1]
    fig, ax = plt.subplots(figsize=(7.6 if blog else 6.4, 4.4 if blog else 3.6), facecolor=BG)
    yy = np.arange(len(V))
    ax.barh(yy, [d["open_sites"] for d in V], color=[POOL if d["region"] == "South West" else POOLL for d in V], height=.62, label="working")
    ax.barh(yy, [d["closed_sites"] for d in V], left=[d["open_sites"] for d in V], color=CORAL, alpha=.6, hatch="///", edgecolor="white", height=.62, label="closed or disused")
    for i, d in enumerate(V):
        t = f"{d['open_sites']}" + (f"   ({d['open_per_million']:.1f} per million)" if d["open_per_million"] != "" else "")
        ax.text(d["open_sites"] + d["closed_sites"] + .4, i, t, va="center", fontsize=9.5 if blog else 7.5, color=FG)
    ax.set_yticks(yy); ax.set_yticklabels([d["region"] for d in V], fontsize=10 if blog else 8)
    ax.set_xlim(0, 40); ax.set_xlabel("open-air pools on the map today", fontsize=10 if blog else 8)
    ax.legend(frameon=False, loc="lower right", fontsize=10 if blog else 8)
    style(ax, "x"); fig.tight_layout(); save(fig, "regions", blog)


for b in (False, True):
    fig_map(b); fig_decades(b); fig_curve(b); fig_comeback(b); fig_regions(b)
from PIL import Image
for f in os.listdir(BLOG):
    if f.startswith("b_") and f.endswith(".png"):
        im = Image.open(os.path.join(BLOG, f)); w, h = im.size
        if w != 1520: im.resize((1520, round(h * 1520 / w)), Image.LANCZOS).save(os.path.join(BLOG, f), optimize=True)
print("figures written")
