# The lido boom and bust

Britain's open-air pools: the 1930s lido boom, the closures from the 1970s and the comeback. There is no open national list of lidos with dates, so this study builds the best open register I could from English Wikipedia, Wikidata and OpenStreetMap, follows each pool from opening to today, and maps every working open-air pool, lido and tidal pool that OpenStreetMap's mappers have tagged.

**Interactive version:** https://tristan-hotham.github.io/lido-boom/

This repository holds the interactive page, derived data and the analysis code for the data study *The lido boom and bust: Britain's open-air pools, 1815 to 2026* by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Paper and archived release: https://doi.org/10.5281/zenodo.23729646

## Headline results

- The register holds {{register.n|int}} lidos and open-air pools ({{register.london|int}} in London). {{register.with_open_decade|int}} have a documented opening year or decade: {{openings.d1930s|int}} of them ({{openings.share_peak|pct0}}) opened in the 1930s, {{openings.y1935|int}} in 1935 alone. Wikipedia says {{published.built_1930s|int}} lidos were built in the 1930s, so the register holds about {{thirties.share_of_169|pct0}} of them.
- {{closures.n_dated|int}} pools have a documented closing year or decade; {{closures.n_1970_1999|int}} ({{closures.share_1970_1999|pct0}}) closed between 1970 and 1999, most in the 1990s ({{closures.d1990s|int}}). Pools that closed had been open for a median of {{closures.median_years_open|int}} years.
- Of the {{fate.ever_closed|int}} pools of known fate that closed at some point, {{fate.closed_then_reopened|int}} ({{fate.share_closed_reopened|pct0}}) have reopened, {{reopenings.since_2000|int}} of them since 2000, after a median of {{reopenings.median_years_shut|int}} years shut (Thames Lido in Reading: {{reopenings.max_years_shut|int}} years).
- Among the {{curve.n|int}} documented pools with a full timeline, the number open peaked at {{curve.peak_open|int}} in {{curve.peak_year|raw}}, fell to {{curve.low_open|int}} in {{curve.low_year|raw}} and is {{curve.open_2026|int}} in 2026.
- I can place {{combined.open|int}} working open-air pools, lidos and tidal pools in the UK today ({{combined.england_open|int}} in England, against {{published.open_england|int}} open in England according to Wikipedia). {{combined.share_south|pct0}} are in London, the South East and the South West; {{combined.share_coastal_open|pct0}} are within 2 km of the sea. The South West has {{combined.top_per_million|f1}} per million residents.
- OpenStreetMap tags {{osm.open_tidal|int}} working tidal and sea pools, {{osm.tidal_cornwall|int}} of them in Cornwall.

## Files

- `index.html`: the interactive page (Leaflet map with a year slider and play button, status filters and search; charts; the register as a sortable table).
- `header.png`: social card.
- `data/lidos.csv`: the register, one row per lido or open-air pool: name, place, region, county, position and its source, distance to the coast, opening, closing and reopening years (or decades), status in 2026, water, linked OpenStreetMap site, sources with URLs, a short quotation or paraphrase of the evidence, and notes.
- `data/osm_sites.csv` and `data/osm_features.csv`: OpenStreetMap features kept as open-air pools, lidos or tidal pools, and the sites they were merged into (features within 400 m), with status (working, disused, unclear), region and coast distance.
- `data/sites.geojson`: the map layer (register entries plus OpenStreetMap-only sites).
- `data/decades.csv`: register openings, closures and reopenings per decade. `data/regions.csv`: working and closed pools by region with Census 2021 rates.
- `data/page_data.json`: compact data for the page. `data/results.json`: every number quoted on the page, in the paper, the blog post and the collage.
- `code/`: Python scripts, run in order: `01_osm.py` (OpenStreetMap open-air pools), `02_register.py` (the register from `register_manual.csv`, positions, regions, map layer), `03_analysis.py` (all statistics), `04_build_site.py` (page and README), `05_header.py` (social card), `06_release_figs.py` (paper and blog figures), `07_paper.py` (paper PDF via xelatex), `08_release.py` (blog post and Zenodo files). `code/register_manual.csv` is the hand-built register with its evidence; `code/common.py` holds shared helpers.
- `release/`: paper PDF and LaTeX source, blog post and figures, Zenodo files. `reddit/`: collage and post text.

## Method in brief

**Register.** I searched the {{wikipedia_articles|int}} English Wikipedia articles in my extracts (lido articles, seaside towns, London parks and others) for lidos, open-air pools, bathing pools and tidal pools, read each mention, and recorded opening, closing and reopening years with a short quotation as evidence. Wikidata items in lido and open-air pool classes and OpenStreetMap `start_date` tags add a few dates. "Closed" is the closure after which a pool stood empty longest. Status in 2026 is what the sources say; where they are silent, OpenStreetMap decides (a working pool mapped on the spot), otherwise it is unknown ({{register.unknown|int}} entries). Positions come from Wikipedia, Wikidata or OpenStreetMap; {{register.approx_positions|int}} entries use the OS Open Names point of their town or district and are flagged as approximate.

**OpenStreetMap.** Features in the UK whose name contains lido, open-air pool, outdoor pool, bathing pool, tidal pool or sea pool, plus public-access swimming pools tagged outdoor, excluding cafés, car parks, streets, hotels, holiday parks, schools, private clubs and paddling pools. Features within 400 m are one site. A site is working if it has a pool-type tag and nothing marks it disused.

**Geography.** Region and nearest place: nearest OS Open Names populated place (Northern Ireland: points west of 5.4 W with no Great Britain place within 15 km). Coastal: within 2 km of the Natural Earth 1:10m coastline. Rates per million use Census 2021 usual residents (England and Wales only).

**Caveats.** This is a documented sample, not a census. Survivors, listed pools and campaign successes are far better documented than pools that closed quietly decades ago, so closures and the decline are understated and comebacks overstated; the timing of openings and closures is more reliable than the shares. OpenStreetMap coverage reflects mappers, not pools: the map of working pools is a floor.

## How to rerun

Python 3 with numpy, scipy, shapely and matplotlib (Playwright for the header, xelatex for the paper). From `code/`: `python3 01_osm.py && python3 02_register.py && python3 03_analysis.py && python3 04_build_site.py`. Inputs are read one folder up and are not included: `_data12/wd_osm_bundle12.json.gz` (OpenStreetMap and Wikidata via QLever, retrieved 28 October 2026), `_data12/wikipedia_batch12*.json.gz` and `_data11/wikipedia_batch11.json.gz` (English Wikipedia wikitext), `osnames_gb.tsv` (OS Open Names), `_data8/census/` (Census 2021 TS001) and `_data3/ne/` (Natural Earth coastline).

## Sources and licence

- English Wikipedia (CC BY-SA 4.0): chiefly "History of lidos in the United Kingdom" and "Lido (swimming pool)", the articles on individual lidos (Banbury Lido, Beccles Lido, Brockwell Lido, Charlton Lido, Cleveland Pools, Droitwich Spa Lido, Finchley Lido, Grange Lido, Hilsea Lido, Jubilee Pool, Parliament Hill Lido, Peterborough Lido, Ruislip Lido, Saltdean Lido, Sandford Parks Lido, Teignmouth Lido, Thames Lido, The Lido, Bristol, Tinside Lido, Tooting Bec Lido, Tropicana, Weston-super-Mare) and town and park articles (Aldershot, Blackpool, Brighton, Bude, Burntisland, Caerleon, Calverton, Cleethorpes, Clevedon, Gourock, Hastings, Margate, Milford Haven, New Brighton, Portobello, Prestatyn, Skegness, Stonehaven, Tynemouth, Uxbridge, Victoria Park, Westward Ho!, Whitehawk), retrieved October 2026. Each register entry names its articles and links them.
- Wikidata (CC0).
- OpenStreetMap, © OpenStreetMap contributors, Open Database Licence (ODbL), via QLever.
- OS Open Names, Ordnance Survey, Open Government Licence v3.0. Contains OS data © Crown copyright and database right 2026.
- Census 2021 TS001: Office for National Statistics, Open Government Licence v3.0.
- Coastline: Natural Earth (public domain). Base map tiles on the page: Esri. Map library: Leaflet.

Because the register quotes and derives from Wikipedia text (CC BY-SA 4.0), the derived data and the page text are released under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/); the OpenStreetMap-derived tables (`osm_sites.csv`, `osm_features.csv` and the OpenStreetMap layer of `sites.geojson`) are also made available under the ODbL as OpenStreetMap requires. Code is MIT (see `LICENSE`).

Companion study: [Did the railway make the seaside?](https://tristan-hotham.github.io/seaside-railways/)

## Citation

Hotham, T. (2026) *The lido boom and bust: Britain's open-air pools, 1815 to 2026*. Zenodo. https://doi.org/10.5281/zenodo.23729646

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
