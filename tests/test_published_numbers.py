"""Figures this repository publishes, recomputed from the files it ships.

README.md, docs/VALIDATION.md and docs/RUBRIC.md quote numbers that came out of
data/robustness_report.json, data/accuracy_report.json, data/corpus_manifest.csv
and the two calibration CSVs. All five are committed. None of the prose around
them was ever compared to them, and a document naming a count that nothing
recomputes is how four files here went stale in one week. One of these has
drifted before: VALIDATION.md said four standard library disagreements when
there were seven, and it was reconciled by hand.

These are not the corpus tests. Those need the 342 MB of recordings and carry
the slow marker. Everything here reads a committed file, so it runs by default
and in CI, which has no fixtures.
"""

import csv
import json
import re
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
VALIDATION = ROOT / "docs" / "VALIDATION.md"
RUBRIC = ROOT / "docs" / "RUBRIC.md"

ROBUSTNESS = json.loads((ROOT / "data" / "robustness_report.json").read_text(encoding="utf-8"))
ACCURACY = json.loads((ROOT / "data" / "accuracy_report.json").read_text(encoding="utf-8"))

WORDS = {1: "one", 2: "two", 3: "three", 7: "seven", 9: "nine"}


def says(path: Path, *phrases: str) -> None:
    body = path.read_text(encoding="utf-8")
    for phrase in phrases:
        assert phrase in body, f"{path.name} should say {phrase!r}"


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / "data" / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def abort_reasons() -> Counter:
    """What each aborted domain came back with, as a status or a transport word."""
    counted: Counter = Counter()
    for outcome in ROBUSTNESS["results"].values():
        if outcome == "scored":
            continue
        status = re.search(r"HTTP (\d+)", outcome)
        counted[status.group(1) if status else outcome.split("unreachable: ")[-1]] += 1
    return counted


def test_the_completion_figures_come_from_the_report():
    scored = ROBUSTNESS["by_outcome"]["scored"]
    aborted = ROBUSTNESS["by_outcome"]["aborted"]
    says(
        VALIDATION,
        f"{ROBUSTNESS['domains']} real sites, recorded and replayed.",
        f"| Audited and scored | {scored} |",
        f"| Aborted with a logged reason | {aborted} |",
        f"the {aborted} is the tool failing",
    )
    says(README, f"{scored} scored, zero crashes")


def test_the_abort_breakdown_adds_up_to_what_the_report_holds():
    """Three rows and eight details, all hand typed beside a committed counter."""
    seen = abort_reasons()
    # The grouping is the document's editorial call. The counts are not.
    refused = sum(seen[s] for s in ("403", "401", "406", "451", "202"))
    gone = sum(seen[s] for s in ("404", "410"))
    unavailable = sum(seen.values()) - refused - gone
    five_hundreds = sum(n for status, n in seen.items() if status.startswith("5"))

    says(
        VALIDATION,
        f"| Refused deliberately | {refused} |",
        f"| Unavailable to this client | {unavailable} |",
        f"| Gone | {gone} |",
        f"{seen['403']} x 403",
        f"{seen['timeout']} timeouts",
        f"{seen['network: ConnectError']} connection errors",
        f"{seen['429']} x 429",
        f"and {WORDS[five_hundreds]} 5xx",
        f"{seen['404']} x 404 and {WORDS[seen['410']]} 410",
    )
    # The same 403 count carries the largest gap this tool admits to.
    says(RUBRIC, f"{seen['403']} sites")
    says(VALIDATION, f"{seen['403']} sites in this run refused")


def test_the_agreement_figures_come_from_the_accuracy_run():
    literal = ACCURACY["tool_vs_literal"]
    stdlib = ACCURACY["tool_vs_stdlib"]
    says(
        VALIDATION,
        f"| Literal reader | {literal['share']:.2f}% |",
        f"| Standard library | {stdlib['share']:.2f}% |",
        f"The {WORDS[len(stdlib['disagreements'])]} standard library disagreements",
    )
    says(README, f"{ACCURACY['verdicts']} verdicts")


def test_the_manifest_sentence_matches_the_manifest():
    manifest = rows("corpus_manifest.csv")
    hashed = sum(1 for row in manifest if row["robots_sha256"])
    says(
        VALIDATION,
        f"{len(manifest)} rows, one per domain",
        f"{hashed} domains",
        f"the other {len(manifest) - hashed} either aborted",
    )


def test_the_sectioning_thresholds_come_from_the_calibration():
    """Five numbers in one paragraph, all from one CSV, none of them checked."""
    pages = rows("block_calibration.csv")
    prose = sorted(
        float(page["largest_share"]) for page in pages if int(page["total_words"]) >= 200
    )
    wall = 100 * sum(1 for share in prose if share >= 0.80) / len(prose)
    says(
        RUBRIC,
        f"Measuring {sum(int(p['blocks']) for p in pages)} blocks across {len(pages)}",
        f"Across the {len(prose)} pages",
        f"the median is {statistics.median(prose):.2f}",
        f"a quarter sit at or below {statistics.quantiles(prose, n=4)[0]:.2f}",
        f"and {wall:.0f} percent",
    )


def test_the_javascript_thresholds_come_from_the_calibration():
    """Stated in RUBRIC.md, in CLAUDE.md, and in a caveat printed to every user."""
    pages = rows("js_calibration.csv")
    client = sorted(int(p["text_chars"]) for p in pages if p["expected"] == "client")
    server = [p for p in pages if p["expected"] == "server"]
    news = sorted(float(p["script_over_text"]) for p in server)
    # Three cuts caught and one missed is the shape RUBRIC.md describes, and the
    # paragraph stops making sense without it. Named here so a changed CSV says so
    # rather than raising an index error four lines down.
    assert len(client) == 4, f"the CSV now labels {len(client)} pages client rendered"

    says(
        RUBRIC,
        f"sampled {len(pages)} live pages",
        f"{client[0]}, {client[1]} and {client[2]} characters",
        f"came in below {min(int(p['text_chars']) for p in server)}",
        f"{news[-2]:.0f} and {news[-1]:.0f}",
        f"sat below {int(news[-3]) + 1}",
        f"it ships {client[3]} characters of",
    )
