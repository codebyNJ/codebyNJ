#!/usr/bin/env python3
"""Draws the profile cards in cards/ from the GitHub and LeetCode APIs.

Run by .github/workflows/cards.yml every day, so visitors only ever load static SVGs.
Locally: GITHUB_TOKEN=$(gh auth token) python3 scripts/cards.py
Stdlib only. Colours and type follow nijeeshnj.tech.
"""
import datetime as dt
import json
import os
import urllib.request
from html import escape

GH_USER = "codebyNJ"
LC_USER = "Nijeesh_1805"
SKIP_LANGS = {"HTML", "CSS", "Jupyter Notebook", "SCSS"}
OUT = os.path.join(os.path.dirname(__file__), "..", "cards")

THEMES = {
    "light": dict(card="#ffffff", line="#ebebeb", ink="#0a0a0a", ink2="#3a3a3a", ink3="#6e6e6e",
                  track="#f1f1f1",
                  easy="#1c6b44", med="#c28a00", hard="#9c2a49"),
    "dark": dict(card="#0f0f0f", line="#1f1f1f", ink="#f7f7f7", ink2="#c2c2c2", ink3="#8c8c8c",
                 track="#1f1f1f",
                 easy="#86efac", med="#fde68a", hard="#fda4af"),
}
SANS = "'Instrument Sans',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
SERIF = "'Instrument Serif',Georgia,'Times New Roman',serif"
MONO = "'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def post(url, query, headers):
    req = urllib.request.Request(url, json.dumps({"query": query}).encode(),
                                 {"Content-Type": "application/json", "User-Agent": "profile-cards", **headers})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors"):
        raise SystemExit(f"{url}: {body['errors']}")
    return body["data"]


def github():
    q = """query{user(login:"%s"){createdAt
      pullRequests(states:MERGED){totalCount}
      repositoriesContributedTo(contributionTypes:[COMMIT,PULL_REQUEST,ISSUE]){totalCount}
      repositories(ownerAffiliations:OWNER,isFork:false,first:100){totalCount nodes{stargazerCount
        languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}
      contributionsCollection{totalCommitContributions totalPullRequestContributions totalIssueContributions
        restrictedContributionsCount contributionCalendar{totalContributions}}}}""" % GH_USER
    return post("https://api.github.com/graphql", q,
                {"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}"})["user"]


def leetcode():
    q = f"""query{{allQuestionsCount{{difficulty count}}
      matchedUser(username:"{LC_USER}"){{profile{{ranking}} submitStatsGlobal{{acSubmissionNum{{difficulty count}}}}}}}}"""
    return post("https://leetcode.com/graphql", q, {"Referer": "https://leetcode.com"})


def svg(w, h, t, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f'<style>text{{font-family:{SANS};fill:{t["ink"]}}}.m{{font-family:{MONO};fill:{t["ink3"]};'
            f'font-size:11px;letter-spacing:1.2px}}.s{{font-family:{SERIF};font-size:26px}}'
            f'.n{{font-size:30px;font-weight:600;letter-spacing:-.5px}}.l{{fill:{t["ink2"]};font-size:13px}}</style>'
            f'{body}</svg>')


def panel(x, w, h, t):
    return f'<rect x="{x + .5}" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{t["card"]}" stroke="{t["line"]}"/>'


def head(x, kicker, title):
    return (f'<text class="m" x="{x}" y="34">{escape(kicker)}</text>'
            f'<text class="s" x="{x}" y="68">{escape(title)}</text>')


def k(n):
    return f"{n / 1000:.1f}k" if n >= 10000 else f"{n:,}"


def overview(g, t):
    W, H, PW = 1000, 236, 492
    cc = g["contributionsCollection"]
    stats = [
        (cc["contributionCalendar"]["totalContributions"], "contributions, past year"),
        (cc["totalCommitContributions"] + cc["restrictedContributionsCount"], "commits, past year"),
        (g["pullRequests"]["totalCount"], "pull requests merged"),
        (cc["totalIssueContributions"], "issues, past year"),
        (sum(r["stargazerCount"] for r in g["repositories"]["nodes"]), "stars earned"),
        (g["repositoriesContributedTo"]["totalCount"], "repos contributed to"),
    ]
    body = panel(0, PW, H, t) + head(28, "GITHUB", "Activity")
    for i, (n, lbl) in enumerate(stats):
        x, y = 28 + (i % 3) * 152, 122 + (i // 3) * 70
        body += f'<text class="n" x="{x}" y="{y}">{k(n)}</text><text class="l" x="{x}" y="{y + 22}">{lbl}</text>'

    sizes = {}
    for r in g["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            name = e["node"]["name"]
            if name not in SKIP_LANGS:  # count each repo once, under its main language
                sizes.setdefault(name, [0, e["node"]["color"] or t["ink3"]])[0] += 1
                break
    top = sorted(sizes.items(), key=lambda kv: -kv[1][0])[:8]
    total = sum(v[0] for _, v in top) or 1
    x0 = W - PW
    body += panel(x0, PW, H, t) + head(x0 + 28, "LANGUAGES · SHARE OF REPOS", "Most used")
    bx, bw = x0 + 28, PW - 56
    body += f'<clipPath id="bar"><rect x="{bx}" y="92" width="{bw}" height="10" rx="5"/></clipPath><g clip-path="url(#bar)">'
    cx = bx
    for _, (size, color) in top:
        seg = bw * size / total
        body += f'<rect x="{cx:.1f}" y="92" width="{seg + .5:.1f}" height="10" fill="{color}"/>'
        cx += seg
    body += "</g>"
    for i, (name, (size, color)) in enumerate(top):
        x, y = bx + (i % 2) * (bw / 2), 136 + (i // 2) * 26
        body += (f'<circle cx="{x + 5}" cy="{y - 4}" r="5" fill="{color}"/>'
                 f'<text class="l" x="{x + 18}" y="{y}">{escape(name)}</text>'
                 f'<text class="m" x="{x + bw / 2 - 16}" y="{y}" text-anchor="end">{100 * size / total:.1f}%</text>')
    return svg(W, H, t, body, "GitHub activity and most used languages")


def leet(lc, t):
    W, H = 1000, 196
    solved = {s["difficulty"]: s["count"] for s in lc["matchedUser"]["submitStatsGlobal"]["acSubmissionNum"]}
    avail = {s["difficulty"]: s["count"] for s in lc["allQuestionsCount"]}
    rank = lc["matchedUser"]["profile"]["ranking"]
    body = panel(0, W, H, t) + head(28, "LEETCODE", "Problems solved")
    body += (f'<text x="28" y="146" style="font-size:52px;font-weight:600;letter-spacing:-1.5px">{solved["All"]}</text>'
             f'<text class="m" x="28" y="170">OF {avail["All"]:,} · RANK {rank:,}</text>')
    bx, bw = 300, W - 300 - 28
    for i, d in enumerate(["Easy", "Medium", "Hard"]):
        y = 58 + i * 44
        frac = solved[d] / (avail[d] or 1)
        color = t[{"Easy": "easy", "Medium": "med", "Hard": "hard"}[d]]
        body += (f'<text class="l" x="{bx}" y="{y}" style="fill:{color};font-weight:600">{d}</text>'
                 f'<text class="m" x="{bx + bw}" y="{y}" text-anchor="end">{solved[d]} / {avail[d]:,}</text>'
                 f'<rect x="{bx}" y="{y + 10}" width="{bw}" height="8" rx="4" fill="{t["track"]}"/>'
                 f'<rect x="{bx}" y="{y + 10}" width="{max(8, bw * frac):.1f}" height="8" rx="4" fill="{color}"/>')
    return svg(W, H, t, body, f"LeetCode: {solved['All']} problems solved")


def main():
    os.makedirs(OUT, exist_ok=True)
    g, lc = github(), leetcode()
    cards = {"overview": lambda t: overview(g, t), "leetcode": lambda t: leet(lc, t)}
    for name, draw in cards.items():
        for theme, t in THEMES.items():
            path = os.path.join(OUT, f"{name}-{theme}.svg")
            with open(path, "w") as f:
                f.write(draw(t))
            print("wrote", os.path.relpath(path))


if __name__ == "__main__":
    main()
