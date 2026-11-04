"""Generate the stats panel and project cards for the profile README.

Replaces github-readme-stats (its public instance is down). Runs in the
"generate profile assets" workflow and writes SVGs into the output dir:
  stats.svg          - stats tiles + top languages
  pin-<repo>.svg     - one card per owned, non-fork repo

Usage: python profile_cards.py <out_dir>   (env: GH_USER, GITHUB_TOKEN optional)
"""
import json
import os
import sys
import urllib.request
from xml.sax.saxutils import escape

USER = os.environ.get("GH_USER", "quanw12")
TOKEN = os.environ.get("GITHUB_TOKEN")

BG, BORDER, TEXT, MUTED, ACCENT = "#0d1117", "#30363d", "#e6edf3", "#8b949e", "#58a6ff"
SANS = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
MONO = "'Fira Code', Consolas, monospace"
FALLBACK_COLORS = ["#58a6ff", "#f9c74f", "#43d9ad", "#ff7b72", "#d2a8ff", "#ffa657"]


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


# github/linguist colors for the languages likely to show up here
LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "SQL": "#e38c00", "TSQL": "#e38c00", "PLpgSQL": "#336790", "Jupyter Notebook": "#DA5B0B",
    "HTML": "#e34c26", "CSS": "#663399", "Shell": "#89e051", "Dockerfile": "#384d54",
    "Java": "#b07219", "C++": "#f34b7d", "C": "#555555", "C#": "#178600", "Go": "#00ADD8",
}


def lang_color(name, i=0):
    return LANG_COLORS.get(name, FALLBACK_COLORS[i % len(FALLBACK_COLORS)])


def fmt(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def wrap(text, width=62, lines=2):
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1][: width - 1].rstrip() + "…"
    return out


def svg(w, h, body, extra_style=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <style>
    text {{ font-family: {SANS}; }}
    .fade {{ opacity: 0; animation: fade .6s ease-out forwards; }}
    @keyframes fade {{ to {{ opacity: 1 }} }}
    {extra_style}
  </style>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="{BG}" stroke="{BORDER}"/>
{body}
</svg>
"""


def stats_svg(stats, langs):
    tiles = ""
    for i, (label, value) in enumerate(stats):
        x, y = 40 + (i % 2) * 210, 88 + (i // 2) * 74
        tiles += f"""  <g class="fade" style="animation-delay:{0.15 * i:.2f}s">
    <text x="{x}" y="{y}" fill="{ACCENT}" font-size="30" font-weight="700" font-family="{MONO}">{escape(value)}</text>
    <text x="{x}" y="{y + 24}" fill="{MUTED}" font-size="14">{escape(label)}</text>
  </g>
"""
    total = sum(b for _, b in langs) or 1
    bar, legend, x = "", "", 520.0
    for i, (name, size) in enumerate(langs):
        w = 440 * size / total
        color = lang_color(name, i)
        bar += f'    <rect x="{x:.1f}" y="0" width="{w:.1f}" height="12" fill="{color}"/>\n'
        x += w
        lx, ly = 520 + (i % 2) * 220, 120 + (i // 2) * 30
        legend += f"""  <g class="fade" style="animation-delay:{0.6 + 0.1 * i:.2f}s">
    <circle cx="{lx + 6}" cy="{ly - 5}" r="6" fill="{color}"/>
    <text x="{lx + 20}" y="{ly}" fill="{TEXT}" font-size="14">{escape(name)} <tspan fill="{MUTED}">{100 * size / total:.1f}%</tspan></text>
  </g>
"""
    if not langs:
        legend = f'  <text x="520" y="120" fill="{MUTED}" font-size="14">No language data yet</text>\n'
    body = f"""  <text x="40" y="46" fill="{TEXT}" font-size="20" font-weight="700">GitHub stats</text>
  <text x="520" y="46" fill="{TEXT}" font-size="20" font-weight="700">Top languages</text>
  <line x1="480" y1="30" x2="480" y2="180" stroke="{BORDER}"/>
{tiles}  <clipPath id="barclip"><rect x="520" y="70" width="0" height="12" rx="6">
    <animate attributeName="width" from="0" to="440" dur="1.2s" begin="0.2s" fill="freeze"/></rect></clipPath>
  <rect x="520" y="70" width="440" height="12" rx="6" fill="#21262d"/>
  <g clip-path="url(#barclip)"><g transform="translate(0 70)">
{bar}  </g></g>
{legend}"""
    return svg(1000, 205, body)


def pin_svg(repo):
    desc = repo.get("description") or "No description yet."
    lines = "".join(
        f'  <text x="24" y="{66 + 20 * i}" fill="{MUTED}" font-size="14">{escape(l)}</text>\n'
        for i, l in enumerate(wrap(desc))
    )
    meta, mx = "", 24
    if repo.get("language"):
        lang = repo["language"]
        meta += f'  <circle cx="{mx + 6}" cy="99" r="6" fill="{lang_color(lang)}"/>\n'
        meta += f'  <text x="{mx + 18}" y="104" fill="{MUTED}" font-size="13">{escape(lang)}</text>\n'
        mx += 30 + 8 * len(lang)
    meta += f'  <text x="{mx}" y="104" fill="{MUTED}" font-size="13">★ {fmt(repo["stargazers_count"])}</text>\n'
    meta += f'  <text x="{mx + 60}" y="104" fill="{MUTED}" font-size="13">⑂ {fmt(repo["forks_count"])}</text>\n'
    body = f"""  <g class="fade">
  <path transform="translate(24 24)" fill="{MUTED}" d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"/>
  <text x="48" y="37" fill="{ACCENT}" font-size="17" font-weight="700">{escape(repo["name"])}</text>
{lines}{meta}  </g>"""
    return svg(500, 124, body)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "dist"
    os.makedirs(out, exist_ok=True)

    user = api(f"/users/{USER}")
    repos = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
    commits = api(f"/search/commits?q=author:{USER}&per_page=1")["total_count"]

    langs = {}
    for r in repos:
        for name, size in api(f"/repos/{USER}/{r['name']}/languages").items():
            langs[name] = langs.get(name, 0) + size
    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:6]

    stats = [
        ("Total commits", fmt(commits)),
        ("Public repos", fmt(user["public_repos"])),
        ("Stars earned", fmt(sum(r["stargazers_count"] for r in repos))),
        ("Followers", fmt(user["followers"])),
    ]
    with open(os.path.join(out, "stats.svg"), "w", encoding="utf-8") as f:
        f.write(stats_svg(stats, top))
    for r in repos:
        if r["name"] == USER:
            continue
        with open(os.path.join(out, f"pin-{r['name']}.svg"), "w", encoding="utf-8") as f:
            f.write(pin_svg(r))
    print(f"wrote stats.svg and {len(repos)} pin cards to {out}")


if __name__ == "__main__":
    main()
