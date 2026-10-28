"""Shared helpers for the lido-boom analysis: paths, OSM/Wikidata parsing, regions and distance to the coast.

Inputs are read in place from the shared data folder one level above the project (never copied):
  ../_data12/wd_osm_bundle12.json.gz        OpenStreetMap (ODbL) and Wikidata (CC0) via QLever, retrieved 28 Oct 2026
  ../_data12/wikipedia_batch12*.json.gz     English Wikipedia wikitext (CC BY-SA 4.0)
  ../_data11/wikipedia_batch11.json.gz      English Wikipedia wikitext of seaside towns (CC BY-SA 4.0)
  ../osnames_gb.tsv                         OS Open Names (OGL v3)
  ../_data3/ne/geojson/ne_10m_coastline.geojson   Natural Earth coastline (public domain)
  ../_data8/census/census2021-ts001-rgn.csv       Census 2021 usual residents by region (OGL v3)
"""
import csv, gzip, io, json, math, os, re
import numpy as np
from scipy.spatial import cKDTree
from shapely import wkt as swkt
from shapely.geometry import shape, LineString, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
HIST = os.path.abspath(os.path.join(ROOT, ".."))
DATA = os.path.join(ROOT, "data")
D12 = os.path.join(HIST, "_data12")
K = math.cos(math.radians(54.0))  # local equirectangular scale for Britain


def xy(lat, lon):
    """Approximate planar coordinates in km (good to about 1% across Britain)."""
    return np.c_[np.asarray(lon) * K * 111.32, np.asarray(lat) * 111.32]


_BUNDLE = None


def bundle():
    global _BUNDLE
    if _BUNDLE is None:
        _BUNDLE = json.load(gzip.open(os.path.join(D12, "wd_osm_bundle12.json.gz")))
    return _BUNDLE


def rows(key):
    """Rows of one QLever result as dicts with the leading '?' dropped and RDF quoting removed."""
    t = bundle()["results"][key]["tsv"]
    out = []
    for r in csv.DictReader(io.StringIO(t), delimiter="\t", quoting=csv.QUOTE_NONE):
        out.append({k.lstrip("?"): clean(v) for k, v in r.items()})
    return out


def clean(v):
    if v is None: return ""
    v = v.strip()
    if v.startswith("<") and v.endswith(">"): return v[1:-1]
    m = re.match(r'^"(.*)"(@\w+|\^\^<[^>]+>)?$', v, re.S)
    if m: return m.group(1)
    return v


def centroid(w):
    """Centroid (lat, lon) of an OSM WKT geometry."""
    g = swkt.loads(w)
    c = g.centroid if not g.is_empty else None
    if c is None or c.is_empty:
        c = g.representative_point()
    return round(c.y, 6), round(c.x, 6)


def wd_point(w):
    m = re.match(r"POINT\(([-\d.]+) ([-\d.]+)\)", w or "")
    return (float(m.group(2)), float(m.group(1))) if m else (None, None)


def wikipedia():
    A = {}
    for f in [os.path.join(D12, "wikipedia_batch12.json.gz"), os.path.join(D12, "wikipedia_batch12b.json.gz"),
              os.path.join(HIST, "_data11", "wikipedia_batch11.json.gz")]:
        for k, v in json.load(gzip.open(f))["articles"].items():
            A.setdefault(k, v)
    return A


# ---------- OS Open Names: nearest populated place gives region, county and nearest town ----------
_OSN = None


def osn():
    global _OSN
    if _OSN is None:
        P = []
        with open(os.path.join(HIST, "osnames_gb.tsv")) as f:
            r = csv.DictReader(f, delimiter="\t")
            for d in r:
                if d["type"] == "populatedPlace" and d["local_type"] in ("City", "Town", "Village", "Suburban Area", "Hamlet", "Other Settlement"):
                    P.append((d["name1"], d["local_type"], float(d["lat"]), float(d["lon"]), d["county"] or d["district"], d["region"], d["country"], d["name2"]))
        lat = np.array([p[2] for p in P]); lon = np.array([p[3] for p in P])
        T = [p for p in P if p[1] in ("City", "Town", "Suburban Area", "Village")]
        _OSN = dict(P=P, tree=cKDTree(xy(lat, lon)), T=T,
                    ttree=cKDTree(xy(np.array([p[2] for p in T]), np.array([p[3] for p in T]))))
    return _OSN


def region_of(lat, lon):
    """(region, county, nearest city, town, suburb or village, km to it). Northern Ireland is not in OS Open Names (GB only):
    points west of 5.4 W and south of 55.35 N with no GB populated place within 15 km are Northern Ireland."""
    O = osn()
    d, i = O["tree"].query(xy([lat], [lon])[0])
    dt, it = O["ttree"].query(xy([lat], [lon])[0])
    if lon < -5.4 and 54.0 < lat < 55.35 and d > 15:
        return "Northern Ireland", "", "", None
    p = O["P"][i]; t = O["T"][it]
    reg = p[5]
    if reg == "Eastern": reg = "East of England"
    return reg, p[4], (t[7] or t[0]) if t[6] == "Wales" and t[7] else t[0], round(float(dt), 1)


def town_point(name, county_hint=None, types=("City", "Town", "Village", "Suburban Area", "Other Settlement")):
    """OS Open Names point for a named place (first match, optionally filtered by county or region text)."""
    O = osn()
    c = [p for p in O["P"] if name in (p[0], p[7]) and p[1] in types]
    if county_hint:
        c2 = [p for p in c if county_hint.lower() in (p[4] + " " + p[5]).lower()]
        c = c2 or c
    if not c: raise KeyError(name)
    order = {"City": 0, "Town": 1, "Suburban Area": 2, "Other Settlement": 3, "Village": 4}
    c.sort(key=lambda p: order.get(p[1], 9))
    return c[0][2], c[0][3]


# ---------- coast ----------
_COAST = None


def coast_km(lat, lon):
    """Distance in km to the Natural Earth 1:10m coastline (British Isles)."""
    global _COAST
    if _COAST is None:
        g = json.load(open(os.path.join(HIST, "_data3", "ne", "geojson", "ne_10m_coastline.geojson")))
        segs = []
        for f in g["features"]:
            geom = shape(f["geometry"])
            for ln in (geom.geoms if geom.geom_type == "MultiLineString" else [geom]):
                c = np.array(ln.coords)
                if c[:, 0].max() < -11 or c[:, 0].min() > 2.5 or c[:, 1].max() < 49 or c[:, 1].min() > 61.5: continue
                segs.append(LineString(xy(c[:, 1], c[:, 0])))
        _COAST = unary_union(segs)
    p = xy([lat], [lon])[0]
    return round(_COAST.distance(Point(p)), 2)


REG_ORDER = ["London", "South East", "South West", "East of England", "East Midlands", "West Midlands",
             "North West", "North East", "Yorkshire and the Humber", "Wales", "Scotland", "Northern Ireland"]


def region_pop():
    """Census 2021 usual residents for English regions and Wales (ONS TS001, OGL v3)."""
    p = os.path.join(HIST, "_data8", "census", "census2021-ts001-rgn.csv")
    out = {}
    for r in csv.DictReader(open(p)):
        nm = r.get("geography") or r.get("Geography") or ""
        val = [v for k, v in r.items() if "Total" in k or "total" in k]
        if not val: val = [list(r.values())[-1]]
        nm = {"East": "East of England", "Yorkshire and The Humber": "Yorkshire and the Humber"}.get(nm, nm)
        out[nm] = int(float(val[0]))
    return out
