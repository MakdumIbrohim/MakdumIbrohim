import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

USER = os.environ.get("GITHUB_REPOSITORY_OWNER", "MakdumIbrohim")
SVG_PATH = os.environ.get("SVG_PATH", "profile-card.svg")
PATTERN = re.compile(
    r'(<tspan x="380" y="530">)<tspan class="dots">\. </tspan><tspan class="key">Repos</tspan>:[^\n]*(</tspan>)'
)


def fetch_stats(user: str, token: str = "") -> tuple[int, int, int]:
    headers = {"User-Agent": user, "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    def get_json(url: str):
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)

    profile = get_json(f"https://api.github.com/users/{user}")
    stars = 0
    page = 1
    while True:
        batch = get_json(
            f"https://api.github.com/users/{user}/repos?per_page=100&type=owner&page={page}"
        )
        if not batch:
            break
        stars += sum(int(repo.get("stargazers_count", 0)) for repo in batch)
        if len(batch) < 100:
            break
        page += 1

    return int(profile["public_repos"]), stars, int(profile["followers"])


def render_stats_inner(repos: int, stars: int, followers: int) -> str:
    d_repos = "." * max(2, 7 - len(str(repos)))
    d_stars = "." * max(2, 9 - len(str(stars)))
    d_followers = "." * max(2, 9 - len(str(followers)))
    return (
        f'<tspan class="dots">. </tspan><tspan class="key">Repos</tspan>:<tspan class="dots"> {d_repos} </tspan>'
        f'<tspan class="value">{repos}</tspan> | '
        f'<tspan class="key">Stars</tspan>:<tspan class="dots"> {d_stars} </tspan>'
        f'<tspan class="value">{stars}</tspan> | '
        f'<tspan class="key">Followers</tspan>:<tspan class="dots"> {d_followers} </tspan>'
        f'<tspan class="value">{followers}</tspan>'
    )


def update_svg(svg_text: str, repos: int, stars: int, followers: int) -> str:
    inner = render_stats_inner(repos, stars, followers)
    updated, count = PATTERN.subn(rf"\g<1>{inner}\g<2>", svg_text, count=1)
    if count != 1:
        raise ValueError("Stats row not found in SVG")
    ET.fromstring(updated)
    return updated


def self_test() -> None:
    sample = (
        '<svg xmlns="http://www.w3.org/2000/svg"><text>'
        '<tspan x="380" y="530"><tspan class="dots">. </tspan><tspan class="key">Repos</tspan>:<tspan class="dots"> ..... </tspan>'
        '<tspan class="value">31</tspan> | <tspan class="key">Stars</tspan>:<tspan class="dots"> ....... </tspan>'
        '<tspan class="value">15</tspan> | <tspan class="key">Followers</tspan>:<tspan class="dots"> ....... </tspan>'
        '<tspan class="value">15</tspan></tspan></text></svg>'
    )
    out = update_svg(sample, 34, 16, 14)
    assert ">34<" in out and ">16<" in out and ">14<" in out
    assert out.count("Stars") == 1 and out.count("Followers") == 1
    out_3 = update_svg(sample, 100, 1234, 9)
    assert " .... " in out_3 and " ..... " in out_3 and " ........ " in out_3


def main() -> None:
    if "--test" in sys.argv:
        self_test()
        return

    with open(SVG_PATH, "r", encoding="utf-8") as f:
        svg_text = f.read()

    repos, stars, followers = fetch_stats(USER, os.environ.get("GITHUB_TOKEN", ""))
    updated = update_svg(svg_text, repos, stars, followers)
    if updated != svg_text:
        with open(SVG_PATH, "w", encoding="utf-8") as f:
            f.write(updated)


if __name__ == "__main__":
    main()
