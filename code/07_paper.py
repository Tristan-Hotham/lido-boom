"""Step 7. Build the paper PDF: fill paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Lido_Boom.tex and compile it with xelatex (figures from 06_release_figs.py).
Placeholders: {{path|fmt}} as in 04_build_site.py, with % escaped for LaTeX.
Run: python3 07_paper.py
"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Lido_Boom"
WORDS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split()


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}\\%"
    if f == "f1": return f"{v:.1f}"
    if f == "words": return WORDS[int(v)] if int(v) < len(WORDS) else f"{int(v):,}"
    if f == "Words": w = fmt(v, "words"); return w[0].upper() + w[1:]
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")
g = R["register"]
rows = (f"Register entries & {g['n']}\\\\\nWith an opening year & {g['with_open_year']}\\\\\nWith an opening year or decade & {g['with_open_decade']}\\\\\n"
        f"With a closing year or decade & {g['with_closed_decade']}\\\\\nReopened after closure & {g['reopened']}\\\\\n\\midrule\n"
        f"Open in 2026 & {g['open']}\\\\\nClosed & {g['closed']}\\\\\nTemporarily closed & {g['temporarily_closed']}\\\\\nStatus unknown & {g['unknown']}\\\\\n\\midrule\n"
        f"In London & {g['london']}\\\\\nWithin 2 km of the sea & {g['coastal']}\\\\\nSea-water or tidal & {g['sea_or_tidal']}\\\\\n"
        f"Drawing on Wikipedia text & {g['wikipedia_sourced']}\\\\\nApproximate (town) position & {g['approx_positions']}\\\\\n")
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{The register of documented lidos and open-air pools.}\\label{tab:summary}"
      "\\begin{tabular}{lr}\\toprule & Entries\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(d['name'])} & {d['closed'] or ''} & {d['reopened']} & {(d['reopened'] - d['closed']) if d['closed'] else ''}\\\\\n" for d in R["reopenings"]["list"])
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{Register pools that closed and reopened. Closed: the closure after which the pool stood empty longest (blank: year not documented).}\\label{tab:reopen}"
      "\\begin{tabular}{lrrr}\\toprule Pool & Closed & Reopened & Years shut\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(d['region'])} & {d['register_entries']} & {d['register_opened_1930s']} & {d['open_sites']} & {d['closed_sites']} & "
               f"{(format(d['open_per_million'], '.1f')) if d['open_per_million'] != '' else ''}\\\\\n" for d in R["regions"])
TG = ("\\begin{table}[tbp]\\centering\\small\\caption{Register entries and pools on today's map by region. Working and closed: register entries plus OpenStreetMap-only sites. Rate: working pools per million residents, Census 2021 (England and Wales only).}\\label{tab:regions}"
      "\\begin{tabular}{lrrrrr}\\toprule Region & Register & Opened 1930s & Working & Closed & Per million\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
s = open(os.path.join(HERE, "paper_template.tex")).read()
s = s.replace("{{TABLE_SUMMARY}}", TS).replace("{{TABLE_REOPEN}}", TR).replace("{{TABLE_REGIONS}}", TG)
s = re.sub(r"\{\{(.+?)\}\}", sub, s)
assert "{{" not in s
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(s)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
print(r.stdout[-400:])
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.move(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
