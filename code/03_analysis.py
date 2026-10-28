"""Step 3. Every number used on the page, in the paper, the blog post and the collage -> ../data/results.json.
Also writes ../data/decades.csv, ../data/regions.csv and ../data/page_data.json (compact data for the page).
Run: python3 03_analysis.py
"""
import csv, json, os, statistics as st
from collections import Counter
import common as C

L = list(csv.DictReader(open(os.path.join(C.DATA, "lidos.csv"))))
O = list(csv.DictReader(open(os.path.join(C.DATA, "osm_sites.csv"))))
G = json.load(open(os.path.join(C.DATA, "sites.geojson")))["features"]
iv = lambda v: int(v) if v not in ("", None) else None
for r in L:
    for k in ("opened", "opened_decade", "closed", "closed_decade", "closed_by", "reopened", "ever_closed", "years_open_before_closure", "years_shut"):
        r[k] = iv(r[k])
    r["coast_km"] = float(r["coast_km"])
R = {}
share = lambda a, b: round(a / b, 4) if b else None

# ---------------- register overview ----------------
N = len(L)
stat = Counter(r["status_2026"] for r in L)
R["register"] = dict(n=N, open=stat["open"], closed=stat["closed"], temporarily_closed=stat["temporarily closed"], unknown=stat["unknown"],
                     known_status=N - stat["unknown"], with_open_year=sum(1 for r in L if r["opened"]),
                     with_open_decade=sum(1 for r in L if r["opened_decade"]),
                     with_closed_year=sum(1 for r in L if r["closed"]), with_closed_decade=sum(1 for r in L if r["closed_decade"]),
                     reopened=sum(1 for r in L if r["reopened"]),
                     wikipedia_sourced=sum(1 for r in L if "WP:" in r["source"]),
                     approx_positions=sum(1 for r in L if "approximate" in r["position_source"]),
                     london=sum(1 for r in L if r["region"] == "London"),
                     coastal=sum(1 for r in L if r["setting"] == "coastal"),
                     sea_or_tidal=sum(1 for r in L if r["water"] in ("sea", "tidal")),
                     tidal=sum(1 for r in L if r["water"] == "tidal"),
                     earliest=min((r["opened"], r["name"]) for r in L if r["opened"])[0],
                     earliest_name=min((r["opened"], r["name"]) for r in L if r["opened"])[1])

# ---------------- openings, closures, reopenings by decade ----------------
dec_open = Counter(r["opened_decade"] for r in L if r["opened_decade"])
dec_close = Counter(r["closed_decade"] for r in L if r["closed_decade"])
dec_re = Counter(r["reopened"] // 10 * 10 for r in L if r["reopened"])
decs = list(range(1810, 2030, 10))
rows = [dict(decade=d, opened=dec_open.get(d, 0), closed=dec_close.get(d, 0), reopened=dec_re.get(d, 0)) for d in decs]
with open(os.path.join(C.DATA, "decades.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
R["decades"] = [r for r in rows if r["decade"] >= 1900]
nd = sum(dec_open.values())
pk = max(dec_open.items(), key=lambda x: x[1])
R["openings"] = dict(n_dated=nd, peak_decade=pk[0], peak_n=pk[1], share_peak=share(pk[1], nd),
                     d1920s=dec_open.get(1920, 0), d1930s=dec_open.get(1930, 0), d1900s_1910s=dec_open.get(1900, 0) + dec_open.get(1910, 0),
                     before_1900=sum(v for d, v in dec_open.items() if d < 1900), after_1945=sum(v for d, v in dec_open.items() if d >= 1950),
                     interwar=sum(1 for r in L if r["opened"] and 1919 <= r["opened"] <= 1939) + sum(1 for r in L if not r["opened"] and r["opened_decade"] in (1920, 1930)),
                     y1935=sum(1 for r in L if r["opened"] == 1935), y1937=sum(1 for r in L if r["opened"] == 1937))
nc = sum(dec_close.values())
pkc = max(dec_close.items(), key=lambda x: (x[1], -x[0]))
R["closures"] = dict(n_dated=nc, peak_decade=pkc[0], peak_n=pkc[1], d1970s=dec_close.get(1970, 0), d1980s=dec_close.get(1980, 0),
                     d1990s=dec_close.get(1990, 0), d2000s=dec_close.get(2000, 0), d2010s=dec_close.get(2010, 0),
                     n_1970_1999=sum(v for d, v in dec_close.items() if 1970 <= d <= 1990), share_1970_1999=share(sum(v for d, v in dec_close.items() if 1970 <= d <= 1990), nc),
                     n_1980_1999=sum(v for d, v in dec_close.items() if 1980 <= d <= 1990),
                     closed_by=sum(1 for r in L if r["closed_by"]),
                     median_years_open=st.median([r["years_open_before_closure"] for r in L if r["years_open_before_closure"]]),
                     n_years_open=sum(1 for r in L if r["years_open_before_closure"]),
                     storms=["Cleethorpes 1978", "New Brighton 1990"])
re_ = [r for r in L if r["reopened"]]
R["reopenings"] = dict(n=len(re_), since_2000=sum(1 for r in re_ if r["reopened"] >= 2000), d1990s=dec_re.get(1990, 0), d2000s=dec_re.get(2000, 0),
                       d2010s=dec_re.get(2010, 0), d2020s=dec_re.get(2020, 0),
                       median_years_shut=st.median([r["years_shut"] for r in L if r["years_shut"]]),
                       n_years_shut=sum(1 for r in L if r["years_shut"]),
                       max_years_shut=max(r["years_shut"] for r in L if r["years_shut"]),
                       max_years_shut_name=max((r["years_shut"], r["name"]) for r in L if r["years_shut"])[1],
                       list=sorted([dict(name=r["name"], closed=r["closed"], reopened=r["reopened"]) for r in re_], key=lambda x: x["reopened"]))
ec = [r for r in L if r["status_2026"] != "unknown"]
R["fate"] = dict(known=len(ec), ever_closed=sum(1 for r in ec if r["ever_closed"]), share_ever_closed=share(sum(1 for r in ec if r["ever_closed"]), len(ec)),
                 never_closed_open=sum(1 for r in ec if not r["ever_closed"] and r["status_2026"] == "open"),
                 closed_then_reopened=sum(1 for r in ec if r["reopened"]),
                 closed_for_good=sum(1 for r in ec if r["status_2026"] == "closed"),
                 share_closed_reopened=share(sum(1 for r in ec if r["reopened"]), sum(1 for r in ec if r["ever_closed"])))
t30 = [r for r in L if r["opened_decade"] == 1930]
k30 = [r for r in t30 if r["status_2026"] != "unknown"]
R["thirties"] = dict(n=len(t30), known=len(k30), open=sum(1 for r in k30 if r["status_2026"] == "open"),
                     open_never_closed=sum(1 for r in k30 if r["status_2026"] == "open" and not r["ever_closed"]),
                     open_after_reopening=sum(1 for r in k30 if r["status_2026"] == "open" and r["reopened"]),
                     closed=sum(1 for r in k30 if r["status_2026"] == "closed"), unknown=len(t30) - len(k30),
                     share_of_169=share(len(t30), 169))

# ---------------- documented pools in use, year by year ----------------
def in_use(r, y):
    o = r["opened"] or (r["opened_decade"] + 5 if r["opened_decade"] else None)
    if o is None or o > y: return None
    c = r["closed"] or (r["closed_decade"] + 5 if r["closed_decade"] else None) or r["closed_by"]
    if r["status_2026"] == "closed" and c is None: return None  # closed at an unknown date: leave out of the curve
    if r["status_2026"] == "unknown" and c is None: return None
    if c is not None and c <= y and not (r["reopened"] and r["reopened"] <= y): return 0
    return 1
TL = [r for r in L if in_use(r, 2026) is not None]
curve = [dict(year=y, open=sum(1 for r in TL if in_use(r, y) == 1), shut=sum(1 for r in TL if in_use(r, y) == 0)) for y in range(1900, 2027)]
R["curve"] = dict(n=len(TL), peak_open=max(c["open"] for c in curve), peak_year=min(c["year"] for c in curve if c["open"] == max(c["open"] for c in curve)),
                  low_year=None, open_1939=[c for c in curve if c["year"] == 1939][0]["open"], open_1970=[c for c in curve if c["year"] == 1970][0]["open"],
                  open_1995=[c for c in curve if c["year"] == 1995][0]["open"], open_2026=[c for c in curve if c["year"] == 2026][0]["open"],
                  shut_1995=[c for c in curve if c["year"] == 1995][0]["shut"], shut_2026=[c for c in curve if c["year"] == 2026][0]["shut"])
after = [c for c in curve if c["year"] >= R["curve"]["peak_year"]]
low = min(after, key=lambda c: (c["open"], c["year"]))
R["curve"]["low_year"] = low["year"]; R["curve"]["low_open"] = low["open"]
R["curve"]["max_shut"] = max(c["shut"] for c in curve); R["curve"]["max_shut_year"] = min(c["year"] for c in curve if c["shut"] == R["curve"]["max_shut"])

# ---------------- OpenStreetMap today ----------------
op = [s for s in O if s["status_osm"] == "open"]
R["osm"] = dict(sites=len(O), open=len(op), disused=sum(1 for s in O if s["status_osm"] == "disused"), unclear=sum(1 for s in O if s["status_osm"] == "unclear"),
                open_lido=sum(1 for s in op if s["kind"] == "lido"), open_openair=sum(1 for s in op if s["kind"] == "open-air"), open_tidal=sum(1 for s in op if s["kind"] == "tidal"),
                open_coastal=sum(1 for s in op if float(s["coast_km"]) <= 2), share_open_coastal=share(sum(1 for s in op if float(s["coast_km"]) <= 2), len(op)),
                open_london=sum(1 for s in op if s["region"] == "London"),
                open_sw=sum(1 for s in op if s["region"] == "South West"), open_se=sum(1 for s in op if s["region"] == "South East"),
                open_scotland=sum(1 for s in op if s["region"] == "Scotland"), open_wales=sum(1 for s in op if s["region"] == "Wales"),
                open_ni=sum(1 for s in op if s["region"] == "Northern Ireland"),
                tidal_cornwall_devon=sum(1 for s in op if s["kind"] == "tidal" and s["county"] in ("Cornwall", "Devon")),
                tidal_cornwall=sum(1 for s in op if s["kind"] == "tidal" and s["county"] == "Cornwall"),
                coastal_sw=sum(1 for s in op if float(s["coast_km"]) <= 2 and s["region"] == "South West"),
                features=sum(int(s["n_features"]) for s in O))
# combined: every place known to have a working open-air pool (register open + OSM-only open)
openall = [f["properties"] for f in G if f["properties"]["status_2026"] == "open"]
closedall = [f["properties"] for f in G if f["properties"]["status_2026"] in ("closed", "temporarily closed")]
reg = Counter(p["region"] for p in openall); regc = Counter(p["region"] for p in closedall)
pop = C.region_pop()
for row in csv.DictReader(open(os.path.join(C.HIST, "_data8", "census", "census2021-ts001-ctry.csv"))):
    if row["geography"] == "Wales": pop["Wales"] = int(row["Residence type: Total; measures: Value"])
regions = []
for g in C.REG_ORDER:
    p = pop.get(g)
    regions.append(dict(region=g, open_sites=reg.get(g, 0), closed_sites=regc.get(g, 0),
                        register_entries=sum(1 for r in L if r["region"] == g),
                        register_opened_1930s=sum(1 for r in L if r["region"] == g and r["opened_decade"] == 1930),
                        osm_open=sum(1 for s in op if s["region"] == g),
                        population_2021=p or "", open_per_million=round(reg.get(g, 0) / p * 1e6, 2) if p else ""))
with open(os.path.join(C.DATA, "regions.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(regions[0].keys())); w.writeheader(); w.writerows(regions)
R["regions"] = regions
eng = [x for x in regions if x["population_2021"] and x["region"] != "Wales"]
top = max(eng, key=lambda x: x["open_per_million"])
R["combined"] = dict(open=len(openall), closed=len(closedall), coastal_open=sum(1 for p in openall if p["setting"] == "coastal"),
                     share_coastal_open=share(sum(1 for p in openall if p["setting"] == "coastal"), len(openall)),
                     london_open=reg.get("London", 0), sw_open=reg.get("South West", 0), se_open=reg.get("South East", 0),
                     south_open=reg.get("London", 0) + reg.get("South West", 0) + reg.get("South East", 0),
                     share_south=share(reg.get("London", 0) + reg.get("South West", 0) + reg.get("South East", 0), len(openall)),
                     north_open=reg.get("North West", 0) + reg.get("North East", 0) + reg.get("Yorkshire and the Humber", 0),
                     top_region=top["region"], top_per_million=top["open_per_million"],
                     sw_coastal_open=sum(1 for p in openall if p["setting"] == "coastal" and p["region"] == "South West"),
                     england_open=sum(reg.get(g, 0) for g in C.REG_ORDER[:9]))
# ---------------- Wikidata coverage ----------------
wd = {}
for r in C.rows("wd_lidos"):
    q = r["s"].rsplit("/", 1)[-1]; wd.setdefault(q, set()).add(r.get("inc", "")[:4])
R["wikidata"] = dict(items=len(wd), with_inception=sum(1 for v in wd.values() if any(v)))
# ---------------- published figures quoted from Wikipedia (text on disk) ----------------
R["published"] = dict(built_1930s=169, open_england=127, lcc_lidos=13, scotland_remaining=3, finchley_record=11962, finchley_record_date="11 July 1971",
                      tooting_yards="100 by 33", jubilee_1935_visitors=60000, new_brighton_cost=90000, cleveland_built=1815)
R["osm"]["tidal_cornwall_names"] = sorted(s["name"] for s in op if s["kind"] == "tidal" and s["county"] == "Cornwall")
R["osm"]["tidal_names"] = sorted((s["name"], s["nearest_town"], s["county"]) for s in op if s["kind"] == "tidal")
R["wikipedia_articles"] = len(C.wikipedia())
R["examples"] = {r["id"]: dict(name=r["name"], opened=r["opened"], closed=r["closed"], reopened=r["reopened"], status=r["status_2026"]) for r in L}
json.dump(R, open(os.path.join(C.DATA, "results.json"), "w"), indent=1, ensure_ascii=False)

# ---------------- page data ----------------
cols = ["id", "name", "place", "region", "lat", "lon", "layer", "status", "opened", "od", "closed", "cd", "cb", "reopened", "water", "setting", "kind", "pos", "src", "ev", "notes"]
prow = []
for f in G:
    p = f["properties"]; lon, lat = f["geometry"]["coordinates"]
    prow.append([p["id"], p["name"], p.get("place", ""), p["region"], round(lat, 4), round(lon, 4), p["layer"], p["status_2026"],
                 iv(p.get("opened", "")), iv(p.get("opened_decade", "")), iv(p.get("closed", "")), iv(p.get("closed_decade", "")), iv(p.get("closed_by", "")),
                 iv(p.get("reopened", "")), p.get("water", ""), p.get("setting", ""), p.get("kind", ""),
                 "approx" if "approximate" in p.get("position_source", "") else "", p.get("source", ""), p.get("evidence", ""), p.get("notes", "")])
json.dump(dict(cols=cols, rows=prow, curve=curve), open(os.path.join(C.DATA, "page_data.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print(json.dumps({k: R[k] for k in ("register", "openings", "closures", "reopenings", "fate", "thirties", "curve", "osm", "combined", "wikidata")}, indent=1))
for x in regions: print(x)
