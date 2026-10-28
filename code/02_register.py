"""Step 2. Build the documented register of lidos and open-air pools, and the combined map layer.

Input: register_manual.csv (in this folder), my hand-built register. Every row cites where its years and status
come from: an English Wikipedia article in the on-disk extract (WP:<title>), a Wikidata item, or OpenStreetMap
tags. The 'evidence' column quotes or closely paraphrases the source text. Positions ('coord') come from:
  wp:<title>   the article's coordinates in the Wikipedia extract
  wd:<QID>     the Wikidata coordinate
  osm:<name>   the OpenStreetMap site of that name from step 1 (nearest, if more than one)
  osn:<name>|<hint>  the OS Open Names point of the town or district (approximate, flagged)
Outputs:
  ../data/lidos.csv        one row per register entry with position, region, coast distance and derived fields
  ../data/sites.geojson    register entries plus OpenStreetMap-only open-air pools (no dates) for the map
Run: python3 02_register.py
"""
import csv, json, os, re
import numpy as np
import common as C

WP = C.wikipedia()
OSM = list(csv.DictReader(open(os.path.join(C.DATA, "osm_sites.csv"))))
WD = {}
for r in C.rows("wd_lidos"):
    q = r["s"].rsplit("/", 1)[-1]
    lat, lon = C.wd_point(r.get("coord", ""))
    if lat is not None: WD[q] = (lat, lon)


RAW = []
for r in C.rows("osm_pools_outdoor"):
    if r.get("location") == "outdoor" or r.get("indoor") == "no" or r.get("covered") == "no" or r.get("swimming_pool") == "outdoor":
        RAW.append(C.centroid(r["wkt"]))
RAWXY = C.xy([a for a, b in RAW], [b for a, b in RAW])


def raw_outdoor_km(lat, lon):
    """Distance to the nearest OSM leisure=swimming_pool tagged outdoor with public-type access (named or not)."""
    return round(float(np.min(np.hypot(*(RAWXY - C.xy([lat], [lon])[0]).T))), 2)


def nearest_osm(lat, lon, name=None, maxkm=0.4):
    best = None
    name, _, town = (name or "").partition("@")
    for s in OSM:
        if name and s["name"] != name: continue
        if town and s["nearest_town"] != town: continue
        d = float(np.hypot(*(C.xy([lat], [lon])[0] - C.xy([float(s["lat"])], [float(s["lon"])])[0])))
        if best is None or d < best[0]: best = (d, s)
    if best and (name or best[0] <= maxkm): return best[1], round(best[0], 2)
    return None, None


def locate(spec):
    kind, _, arg = spec.partition(":")
    if kind == "wp":
        c = WP[arg].get("coord")
        if not c: raise KeyError(arg)
        return c["lat"], c["lon"], "Wikipedia article coordinates"
    if kind == "wd":
        lat, lon = WD[arg]; return lat, lon, f"Wikidata {arg}"
    if kind == "osm":
        s, _ = nearest_osm(54, -2, name=arg)
        if s is None: raise KeyError(arg)
        return float(s["lat"]), float(s["lon"]), "OpenStreetMap feature"
    if kind == "osn":
        nm, _, hint = arg.partition("|")
        lat, lon = C.town_point(nm, hint or None)
        return lat, lon, "OS Open Names place point (approximate)"
    raise ValueError(spec)


def wp_url(src):
    out = []
    for part in [p.strip() for p in re.split(r";\s+(?=WP:|Wikidata|OSM)", src)]:
        if part.startswith("WP:"):
            t = part[3:].strip(); out.append("https://en.wikipedia.org/wiki/" + t.replace(" ", "_"))
        elif part.startswith("Wikidata"):
            out.append("https://www.wikidata.org/wiki/" + part.split()[-1])
    return " ".join(out)


def main():
    rows = list(csv.DictReader(open(os.path.join(C.HERE, "register_manual.csv"))))
    out = []
    used_osm = set()
    for r in rows:
        lat, lon, how = locate(r["coord"])
        s, d = nearest_osm(lat, lon) if not r["coord"].startswith("osm:") else nearest_osm(54, -2, name=r["coord"][4:])
        if s is not None: used_osm.add(s["site_id"])
        reg, county, town, _ = C.region_of(lat, lon)
        num = lambda k: int(r[k]) if r[k] else None
        op, cl, ro, cb = num("opened"), num("closed"), num("reopened"), num("closed_by")
        od = op // 10 * 10 if op else (int(r["opened_decade"][:4]) if r["opened_decade"] else None)
        cd = cl // 10 * 10 if cl else (int(r["closed_decade"][:4]) if r["closed_decade"] else None)
        ever_closed = bool(cl or cd or cb or r["status"] == "closed" or ro)
        out.append(dict(
            id=r["id"], name=r["name"], place=r["place"], region=reg, county=county,
            lat=round(lat, 5), lon=round(lon, 5), position_source=how, coast_km=C.coast_km(lat, lon),
            setting="coastal" if C.coast_km(lat, lon) <= 2 else "inland",
            opened=op or "", opened_decade=od or "", closed=cl or "", closed_decade=cd or "", closed_by=cb or "",
            reopened=ro or "", ever_closed=int(ever_closed), status_2026=r["status"], water=r["water"],
            years_open_before_closure=(cl - op) if (cl and op) else "", years_shut=(ro - cl) if (ro and cl) else "",
            osm_outdoor_pool_km=raw_outdoor_km(lat, lon),
            osm_site=s["site_id"] if s is not None else "", osm_status=s["status_osm"] if s is not None else "",
            source=r["source"], source_urls=wp_url(r["source"]), evidence=r["evidence"], notes=r["notes"]))
    k = list(out[0].keys())
    with open(os.path.join(C.DATA, "lidos.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=k); w.writeheader(); w.writerows(out)
    # map layer
    feats = []
    for o in out:
        feats.append(dict(type="Feature", geometry=dict(type="Point", coordinates=[o["lon"], o["lat"]]),
                          properties=dict(layer="register", **{x: o[x] for x in ("id", "name", "place", "region", "opened", "opened_decade", "closed", "closed_decade",
                                                                             "closed_by", "reopened", "status_2026", "water", "setting", "position_source", "source", "evidence", "notes")})))
    extra = 0
    for s in OSM:
        if s["site_id"] in used_osm or s["status_osm"] == "unclear": continue
        extra += 1
        feats.append(dict(type="Feature", geometry=dict(type="Point", coordinates=[float(s["lon"]), float(s["lat"])]),
                          properties=dict(layer="osm", id=s["site_id"], name=s["name"], place=s["nearest_town"], region=s["region"],
                                          status_2026="open" if s["status_osm"] == "open" else "closed", kind=s["kind"],
                                          setting="coastal" if float(s["coast_km"]) <= 2 else "inland", source="OpenStreetMap", osm_ids=s["osm_ids"])))
    json.dump(dict(type="FeatureCollection", features=feats), open(os.path.join(C.DATA, "sites.geojson"), "w"), ensure_ascii=False)
    print(len(out), "register rows;", extra, "OSM-only sites;", len(used_osm), "OSM sites linked")
    for o in out:
        flag = "" if (o["osm_status"] in ("", "unclear") or (o["osm_status"] == "open") == (o["status_2026"] == "open")) else "  <-- status differs from OSM"
        print(f"{o['id']:13s} {o['region'][:14]:14s} {o['opened']!s:5s} {o['closed']!s:5s} {o['reopened']!s:5s} {o['status_2026']:18s} osm={o['osm_site']}:{o['osm_status']} coast={o['coast_km']}{flag}")


if __name__ == "__main__":
    main()
