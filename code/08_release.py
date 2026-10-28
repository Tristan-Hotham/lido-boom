"""Step 8. Blog post (release/blog/post.html from blog_template.html), blog and Zenodo meta files,
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader.
Run: python3 08_release.py
"""
import json, os, re, shutil, zipfile
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "04_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
t = open(os.path.join(HERE, "blog_template.html")).read()
t = re.sub(r"\{\{(?!IMG\|)([^{}]+?)\}\}", b.sub, t)
open(os.path.join(ROOT, "release", "blog", "post.html"), "w").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m

title = "The Lido Boom and Bust: Britain's Open-Air Pools, 1815 to 2026"
o = R["openings"]; c = R["closures"]; rp = R["reopenings"]
meta = dict(
    title="The lido boom and bust: how Britain built, closed and saved its open-air pools",
    slug="lido-boom",
    excerpt=(f"In the 1930s Britain built lidos; from the 1970s it closed them; since 2000 some have come back. I built an open register of "
             f"{R['register']['n']} lidos: {o['d1930s']} of {o['n_dated']} dated openings came in the 1930s, and {rp['n']} closed pools have reopened."),
    seo_description=f"{o['d1930s']} of {o['n_dated']} dated lido openings came in the 1930s; {rp['n']} closed lidos reopened. An open register and map of Britain's open-air pools.",
    tags=["lidos", "swimming", "outdoor swimming", "1930s", "seaside", "heritage", "maps", "data"],
    header_alt=("Title card reading 'The lido boom and bust' on a cream background, beside a map of Britain dotted with lidos and open-air pools: blue for open, "
                f"gold for reopened, coral for closed. Text: {o['d1930s']} of {o['n_dated']} dated openings came in the 1930s; {c['n_1970_1999']} of {c['n_dated']} "
                f"dated closures came in 1970 to 1999; then {rp['n']} came back."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

pt = open(os.path.join(ROOT, "release", "paper", "Hotham_Lido_Boom.tex")).read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%")
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title=title,
    description_html=f"<p>{ab}</p><p>Register derived from English Wikipedia (CC BY-SA 4.0), Wikidata (CC0) and OpenStreetMap (© OpenStreetMap contributors, ODbL); every entry cites its source.</p>"
                     f"<p>Interactive version: https://tristan-hotham.github.io/lido-boom/. Data and code: https://github.com/Tristan-Hotham/lido-boom. Blog post: to follow.</p>",
    keywords=["lidos", "open-air swimming pools", "tidal pools", "leisure history", "interwar Britain", "municipal amenities", "heritage campaigns", "OpenStreetMap", "Wikipedia", "United Kingdom"],
    licence="cc-by-sa-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/lido-boom", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/lido-boom/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://en.wikipedia.org/wiki/History_of_lidos_in_the_United_Kingdom", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://www.wikidata.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.openstreetmap.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ons.gov.uk/census", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.naturalearthdata.com", relation="isderivedfrom", resource_type="dataset"),
    ])
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)
shutil.copy(os.path.join(ROOT, "release", "Hotham_Lido_Boom.pdf"), Z)
for f in ["lidos.csv", "osm_sites.csv", "decades.csv", "regions.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
with zipfile.ZipFile(os.path.join(Z, "lido-boom_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for sub in ("code", "data"):
        for f in sorted(os.listdir(os.path.join(ROOT, sub))):
            p = os.path.join(ROOT, sub, f)
            if os.path.isfile(p) and not f.endswith(".pyc"): zf.write(p, f"lido-boom/{sub}/{f}")
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f"lido-boom/{f}")
print("release files written; post words:", len(re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|.*?\}\}", "", t, flags=re.S)).split()))
