"""The picture at the top of the README has to agree with the recording.

It carries a comment saying every number in it is a real result, and for two
releases it was not: the scoring changed underneath a hand-drawn image and
nothing noticed. The front page is the worst place in this project to be wrong
about its own output, because it is the only part most people read.

So the picture is generated now, and this holds it to what the tool actually
prints for the recorded run.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_output_image as builder

SVG = ROOT / "assets" / "output.svg"
README = ROOT / "README.md"


def text_of(svg: str) -> str:
    """Everything the picture says, with the markup taken out."""
    return " ".join(re.findall(r"<text[^>]*>([^<]*)</text>", svg))


def test_the_picture_matches_the_recorded_run():
    assert SVG.read_text(encoding="utf-8") == builder.render(builder.audit()), (
        "assets/output.svg is behind the recording. Run scripts/build_output_image.py."
    )


def test_the_numbers_in_the_picture_are_the_tools_own():
    payload = builder.audit()
    said = text_of(SVG.read_text(encoding="utf-8"))

    access = payload["scores"]["access"]
    citation = payload["crawlers"]["citation"]

    assert payload["tool"]["version"] in said
    assert f"{access['score']:g}/100  {access['letter']}" in said
    assert f"{citation['allowed']} of {citation['total']} allowed" in said


def test_the_readme_describes_the_picture_it_shows():
    """The alt text repeats the scores, so it goes stale the same way."""
    label = re.search(r'aria-label="([^"]*)"', SVG.read_text(encoding="utf-8"))
    assert label, "the picture lost its aria-label"

    payload = builder.audit()
    access = payload["scores"]["access"]
    wanted = f"Access {access['score']:g} out of 100"

    assert wanted in label.group(1)
    assert wanted in README.read_text(encoding="utf-8"), (
        "the README's alt text no longer matches the picture it describes"
    )
