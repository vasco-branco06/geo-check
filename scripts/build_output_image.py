"""Rewrite assets/output.svg from the recorded run it claims to come from.

The file has said since the first release that every number in it is a real
result and not a mock-up, and that was true when it was drawn by hand. Then the
scoring changed twice and the picture did not, so the README's opening image
spent two releases showing version 0.1.0, Access 56 grade D, and three of six
citation crawlers, against a tool that now says 0.3.0, 67.2 grade C, and five of
eleven.

What is generated here is the content. The design is not: which lines are worth
showing, where a list gets cut, and the fact that it ends by admitting the
report continues are editorial choices, and they stay in this file where a
person can argue with them.

    python scripts/build_output_image.py          rewrite the picture
    python scripts/build_output_image.py --check  say whether it is current

tests/test_output_image.py holds it to the recording, so this going stale again
fails the suite rather than sitting on the front page.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geo_check.checks import run_all
from geo_check.cli import collect_caps
from geo_check.fixtures import Replayer, load
from geo_check.models import Category
from geo_check.report.json_out import build
from geo_check.scoring import score_category
from geo_check.site import build_site

DOMAIN = "nytimes.com"
FIXTURES = ROOT / "tests" / "fixtures" / "golden"
SVG = ROOT / "assets" / "output.svg"

# Terminal geometry. CH is the advance of one monospace character at 13px, which
# is what lets a coloured segment start exactly where the one before it ended.
WIDTH, X0, Y0, LINE, CH = 624, 26.0, 46.0, 21.0, 8.42
COLUMNS = 68

TEXT, MUTED, RULE = "#c9d1d9", "#8b949e", "#30363d"
GREEN, RED, AMBER, BLUE, PURPLE = "#3fb950", "#f85149", "#d29922", "#58a6ff", "#bc8cff"
GRADE = {"A": GREEN, "B": BLUE, "C": AMBER, "D": AMBER, "F": RED}

Row = list[tuple[int, str, str, bool]] | None


def audit() -> dict:
    """The payload, replayed from the recording. Never touches the network."""
    site = build_site(DOMAIN, pages=5, fetcher=Replayer(load(FIXTURES, DOMAIN)["responses"]))
    results = run_all(site)
    return build(
        site,
        results,
        score_category(results, Category.ACCESS, caps=collect_caps(site)),
        score_category(results, Category.READABILITY),
    )


def fit(names: list[str], room: int) -> str:
    """Join what fits and say so when the rest did not.

    A blocked list of eleven crawler names is wider than the terminal, and a
    picture that runs off its own edge looks like a bug rather than a crop.
    """
    out: list[str] = []
    for name in names:
        if len(", ".join([*out, name])) + 3 > room and out:
            return ", ".join(out) + ", …"
        out.append(name)
    return ", ".join(out)


def rows(p: dict) -> list[Row]:
    """Every line of the picture, as (column, text, colour, bold) segments.

    None is a blank line. Columns rather than pixels, because the whole point of
    a monospace terminal is that column n is the same place on every row.
    """
    run, scores, crawlers = p["run"], p["scores"], p["crawlers"]
    out: list[Row] = []

    out.append([(0, f"$ geo-check {run['domain']}", GREEN, True)])
    out.append(None)
    out.append([(0, f"{p['tool']['name']} {p['tool']['version']}   {run['domain']}", TEXT, True)])
    out.append([(0, f"{run['base_url']}/   {run['pages_sampled']} pages sampled", MUTED, False)])
    out.append(None)

    for label, key in (("ACCESS", "access"), ("READABILITY", "readability")):
        s = scores[key]
        head = f"  {label}".ljust(16)
        out.append(
            [
                (0, head, TEXT, False),
                (len(head), f"{s['score']:g}/100  {s['letter']}", GRADE[s["letter"]], True),
            ]
        )
    out.append(None)

    t = p["training_posture"]
    posture = f"  Training posture: {t['state']} ({t['allowed']} of {t['total']} allowed)"
    out.append([(0, posture, MUTED, False)])
    out.append(
        [(0, "  Informational only. Blocking model training is a business decision", MUTED, False)]
    )
    out.append([(0, "  and costs no points here.", MUTED, False)])
    out.append(None)
    out.append([(0, "─" * COLUMNS, RULE, False)])

    for title, key in (("CITATION CRAWLERS", "citation"), ("USER FETCH CRAWLERS", "user_fetch")):
        bucket = crawlers[key]
        agents = bucket["agents"]
        allowed = [c["token"] for c in agents if c["allowed"]]
        blocked = [c for c in agents if not c["allowed"]]
        head = f"{title}   {bucket['allowed']} of {bucket['total']} allowed"
        out.append([(0, head, TEXT, True)])
        for word, colour, names in (
            ("allowed", GREEN, allowed),
            ("blocked", RED, [c["token"] for c in blocked]),
        ):
            head = f"  {word}  "
            out.append(
                [
                    (0, head, colour, False),
                    (len(head), fit(names, COLUMNS - len(head)), TEXT, False),
                ]
            )
        # One reason, not six. The report lists them all; the picture is a poster.
        rule = next((c["matched_rule"] for c in blocked if c.get("matched_rule")), None)
        if rule:
            out.append([(0, f"           because of  {rule}"[:COLUMNS], MUTED, False)])
        if key == "citation":
            out.append(None)

    out.append(None)
    out.append([(0, "─" * COLUMNS, RULE, False)])
    out.append([(0, "WHAT TO CHANGE FIRST", TEXT, True)])
    out.append(None)
    out.append([(0, f"  Add these lines to {run['base_url']}/robots.txt:", TEXT, False)])
    out.append(None)

    # The first two stanzas. Whoever needs all eleven will run the tool.
    stanzas = [s for s in (p["robots_txt_additions"] or "").split("\n\n") if s.strip()][:2]
    for index, stanza in enumerate(stanzas):
        for line in stanza.splitlines():
            out.append([(0, "      " + line, PURPLE, False)])
        if index == 0:
            out.append(None)
    out.append(None)

    for c in sorted(p["checks"], key=lambda c: -(c["weight"] * (1 - c["ratio"])))[:3]:
        head = f"{c['weight'] * (1 - c['ratio']):5.1f} points  "
        out.append([(0, head, AMBER, True), (len(head), c["title"], TEXT, False)])
    out.append(None)
    out.append([(0, "  … full report continues, and --output writes it as markdown", MUTED, False)])
    return out


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(p: dict) -> str:
    body = rows(p)
    height = int(Y0 + len(body) * LINE + 26)
    a, r = p["scores"]["access"], p["scores"]["readability"]
    citation = p["crawlers"]["citation"]
    label = (
        f"Terminal output of geo-check auditing {DOMAIN}: "
        f"Access {a['score']:g} out of 100, grade {a['letter']}. "
        f"Readability {r['score']:g} out of 100, grade {r['letter']}. "
        f"{citation['allowed']} of {citation['total']} citation crawlers allowed."
    )

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
            f'width="{WIDTH}" height="{height}" role="img" aria-label="{escape(label)}">'
        ),
        f"<title>geo-check running against {DOMAIN}</title>",
        "<!-- Generated by scripts/build_output_image.py from the recorded response in",
        f"     tests/fixtures/golden/{DOMAIN}.json.gz. Every number here is a real result,",
        "     not a mock-up, and a test fails when this drifts from the recording. -->",
        (
            '<style>text{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,'
            '"Liberation Mono",monospace;font-size:13px;white-space:pre}</style>'
        ),
        f'<rect width="{WIDTH}" height="{height}" rx="10" fill="#0d1117"/>',
        f'<rect width="{WIDTH}" height="30" rx="10" fill="#161b22"/>',
        f'<rect y="20" width="{WIDTH}" height="10" fill="#161b22"/>',
        '<circle cx="20" cy="15" r="5" fill="#ff5f57"/>',
        '<circle cx="38" cy="15" r="5" fill="#febc2e"/>',
        '<circle cx="56" cy="15" r="5" fill="#28c840"/>',
        (
            f'<text x="{WIDTH // 2}" y="19" fill="{MUTED}" text-anchor="middle" '
            'style="font-size:11px">geo-check</text>'
        ),
    ]
    for index, row in enumerate(body):
        if row is None:
            continue
        y = Y0 + index * LINE
        for column, text, colour, bold in row:
            if not text:
                continue
            weight = ' font-weight="600"' if bold else ""
            x = round(X0 + column * CH, 1)
            parts.append(f'<text x="{x}" y="{y:g}" fill="{colour}"{weight}>{escape(text)}</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Rewrite assets/output.svg from the recording.")
    parser.add_argument("--check", action="store_true", help="Exit 1 if the picture is stale.")
    args = parser.parse_args()

    wanted = render(audit())
    current = SVG.read_text(encoding="utf-8") if SVG.exists() else ""

    if args.check:
        if current == wanted:
            print("assets/output.svg is current.")
            return 0
        print("assets/output.svg is behind the recording. Run scripts/build_output_image.py.")
        return 1

    SVG.write_text(wanted, encoding="utf-8", newline="\n")
    print(f"assets/output.svg rewritten from {DOMAIN}. Re-render the PNG from it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
