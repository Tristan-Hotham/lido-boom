"""Step 1. Open-air pools in OpenStreetMap today.

Reads three OSM extracts (QLever, OSM inside the UK, retrieved 28 Oct 2026):
  osm_lidos_named   anything whose name matches lido / bathing pool / open air pool / tidal pool / sea pool / swimming pool
  osm_pools_outdoor leisure=swimming_pool with access yes/public/customers/permissive
  osm_disused_pools disused:/abandoned:/was:/historic:leisure=swimming_pool
and keeps features that are, by name or tags, a public open-air pool, lido or tidal/sea pool. Features within
400 m of each other are merged into one site. Output: ../data/osm_sites.csv (one row per site) and
../data/osm_features.csv (the kept features with their reasons).
Run: python3 01_osm.py
"""
import csv, os, re
import numpy as np
from scipy.sparse.csgraph import connected_components
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree
import common as C

LIDO = re.compile(r"\blidos?\b", re.I)
OPEN = re.compile(r"open[- ]?air|outdoor (swimming )?pool|outdoor swimming|bathing pool|bathing lake|swimming lake", re.I)
TIDAL = re.compile(r"tidal|sea pool|rock ?pool|sea[- ]water baths|marine lake|bathing place", re.I)
# names that contain "lido" etc. but are not a pool: shops, food, streets, car parks, clubs, holiday parks
NOTPOOL = re.compile(r"caf[eé]|restaurant|chef|noodle|chinese|\bbar\b|stores|shop|extra\b|garage|car park|parking|road|close|avenue|lane|\bway\b|terrace|square|rise|place\b|"
                     r"court\b|walk\b|grove|house|hotel|club\b|caravan|holiday|railway|ticket|allotment|gardens?\b|field\b|lodge|grange|farm|entrance|booth|sandpit|"
                     r"paddling|putting|shaft|cottage|office|staff|\bwell\b|\bdog\b|paws|leisure park|working men|entertainment|promenade|deco at|beach stores|\bcentre cafe|theatre", re.I)
RUIN = re.compile(r"disused|unused|ruin|bulldozed|former|\bold\b|\(dry\)|derelict|demolished|now closed", re.I)
POOLISH = {"swimming_pool", "sports_centre", "water_park", "swimming_area", "bathing_place"}
NOTPUBLIC = re.compile(r"staff|dog|school|college|academy|hydrotherapy|hotel|holiday|david lloyd|bannatyne|spa\b|health club|swim school|cottages|caravan|camp\b|kids|paddling|splash|hot tub", re.I)


def keep_named(r):
    nm = r.get("name", "")
    if not nm: return None
    if NOTPOOL.search(nm) and not re.search(r"lido \(|pool", nm, re.I): return None
    if NOTPOOL.search(nm) and re.search(r"paddling|car park|cafe|café|entrance|booth|sandpit|putting|railway|ticket|office|staff|cottage|\bwell\b|\bdog\b|paws", nm, re.I): return None
    kind = "tidal" if TIDAL.search(nm) else "lido" if LIDO.search(nm) else "open-air" if OPEN.search(nm) else None
    if kind is None: return None
    if kind == "lido" and re.search(r"halidon|hellidon|ballidon|polidor|calidor|gellidoc|lilidorei|elidor|helidor|thalido", nm, re.I): return None
    return kind


def main():
    feats = []
    for r in C.rows("osm_lidos_named"):
        kind = keep_named(r)
        if not kind: continue
        lei = r.get("leisure", "")
        if lei and lei not in POOLISH and lei not in ("park", "garden"): continue
        if lei in ("park", "garden"): continue
        lat, lon = C.centroid(r["wkt"])
        dis = bool(RUIN.search(r["name"])) or r.get("disused") == "yes" or r.get("was") == "swimming_pool"
        if r.get("indoor") == "yes" or r.get("covered") == "yes" or r.get("access") == "private": continue
        feats.append(dict(osm=r["osm"], name=r["name"], kind=kind, src="named", leisure=lei, start=r.get("start", ""), wikidata=r.get("wikidata", ""),
                          disused=int(dis), lat=lat, lon=lon, why="name"))
    for r in C.rows("osm_pools_outdoor"):
        outdoor = r.get("location") == "outdoor" or r.get("indoor") == "no" or r.get("covered") == "no" or r.get("swimming_pool") == "outdoor"
        nm = r.get("name", "")
        if not outdoor or not nm: continue
        if NOTPUBLIC.search(nm + " " + r.get("operator", "") + " " + r.get("swimming_pool", "")): continue
        if r.get("swimming_pool") in ("hot_tub", "spa", "personal", "wading", "kids", "paddling_pool", "children's_pool"): continue
        kind = "tidal" if TIDAL.search(nm) else "lido" if LIDO.search(nm) else "open-air"
        lat, lon = C.centroid(r["wkt"])
        feats.append(dict(osm=r["osm"], name=nm, kind=kind, src="outdoor", leisure="swimming_pool", start="", wikidata="",
                          disused=int(bool(RUIN.search(nm))), lat=lat, lon=lon, why="outdoor tag"))
    for r in C.rows("osm_disused_pools"):
        nm = r.get("name", "")
        if not nm or NOTPUBLIC.search(nm): continue
        if not (LIDO.search(nm) or OPEN.search(nm) or TIDAL.search(nm) or re.search(r"outdoor", nm, re.I)): continue
        lat, lon = C.centroid(r["wkt"])
        feats.append(dict(osm=r["osm"], name=nm, kind="tidal" if TIDAL.search(nm) else "lido" if LIDO.search(nm) else "open-air", src="disused",
                          leisure="", start=r.get("start", ""), wikidata="", disused=1, lat=lat, lon=lon, why="disused tag"))
    # de-duplicate exact OSM ids
    seen = {}; F = []
    for f in feats:
        if f["osm"] in seen:
            F[seen[f["osm"]]]["disused"] |= f["disused"]; continue
        seen[f["osm"]] = len(F); F.append(f)
    # merge features within 250 m into sites
    P = C.xy([f["lat"] for f in F], [f["lon"] for f in F])
    pairs = cKDTree(P).query_pairs(0.40, output_type="ndarray")
    n = len(F)
    g = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n)) if len(pairs) else coo_matrix((n, n))
    _, lab = connected_components(g, directed=False)
    sites = []
    for s in sorted(set(lab)):
        mem = [F[i] for i in range(n) if lab[i] == s]
        # best name: prefer a pool-like named feature that is not disused-only
        mem.sort(key=lambda f: (f["src"] != "named", f["leisure"] not in POOLISH, len(f["name"])))
        nm = mem[0]["name"]
        kinds = {f["kind"] for f in mem}
        kind = "tidal" if "tidal" in kinds else "lido" if "lido" in kinds else "open-air"
        active = [f for f in mem if not f["disused"] and (f["leisure"] in POOLISH or f["src"] == "outdoor")]
        status = "open" if active else ("disused" if all(f["disused"] for f in mem) else "unclear")
        lat = float(np.mean([f["lat"] for f in mem])); lon = float(np.mean([f["lon"] for f in mem]))
        reg, county, town, dtown = C.region_of(lat, lon)
        sites.append(dict(site_id=f"osm{s:04d}", name=nm, kind=kind, status_osm=status, lat=round(lat, 5), lon=round(lon, 5),
                          region=reg, county=county, nearest_town=town, coast_km=C.coast_km(lat, lon),
                          start_date="; ".join(sorted({f["start"] for f in mem if f["start"]})),
                          wikidata="; ".join(sorted({f["wikidata"] for f in mem if f["wikidata"]})),
                          n_features=len(mem), osm_ids=" ".join(f["osm"].replace("https://www.openstreetmap.org/", "") for f in mem)))
    for f, l in zip(F, lab): f["site_id"] = f"osm{l:04d}"
    with open(os.path.join(C.DATA, "osm_sites.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sites[0].keys())); w.writeheader(); w.writerows(sites)
    with open(os.path.join(C.DATA, "osm_features.csv"), "w", newline="") as fh:
        k = ["site_id", "osm", "name", "kind", "src", "why", "leisure", "start", "wikidata", "disused", "lat", "lon"]
        w = csv.DictWriter(fh, fieldnames=k); w.writeheader(); w.writerows([{x: f[x] for x in k} for f in F])
    print(len(F), "features ->", len(sites), "sites")
    from collections import Counter
    print(Counter((s["kind"], s["status_osm"]) for s in sites))


if __name__ == "__main__":
    main()
