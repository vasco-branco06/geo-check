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
ASSETS = ROOT / "assets"


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


def elements(svg: str) -> list[str]:
    """Each text element on its own, so a one letter grade can be matched exactly."""
    return [t.strip() for t in re.findall(r"<text[^>]*>([^<]*)</text>", svg)]


def test_every_picture_that_names_the_site_carries_its_current_numbers():
    """Three pictures quote the same run, and two of them went stale unnoticed.

    The terminal image was generated and caught. The banner and the social card
    were drawn by hand, said Access 56 grade D and three of six citation crawlers
    for two releases, and nothing was watching. The social card is the og:image,
    so that one was wrong on every link anybody shared.
    """
    payload = builder.audit()
    access = payload["scores"]["access"]
    citation = payload["crawlers"]["citation"]
    whole = str(int(access["score"]))
    counts = f"{citation['allowed']} of {citation['total']}"

    checked = []
    for svg in sorted(ASSETS.glob("*.svg")):
        body = svg.read_text(encoding="utf-8")
        if "nytimes" not in body:
            continue
        checked.append(svg.name)
        # The aria-label is an attribute, so it is not among the text elements.
        said = body
        assert whole in said, f"{svg.name} does not carry Access {whole}"
        assert counts in said, f"{svg.name} does not say {counts} citation crawlers"
        # The grade is a standalone element in the two cards and glued to the
        # score in the terminal one, so either shape counts.
        letter = access["letter"]
        carried = any(el == letter or el.endswith(f"  {letter}") for el in elements(body))
        assert carried or f"grade {letter}" in body, (
            f"{svg.name} does not carry the grade {letter}"
        )

    assert len(checked) == 3, f"expected three pictures quoting the run, found {checked}"
