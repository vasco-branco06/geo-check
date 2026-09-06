"""Write data/corpus_manifest.csv, a fingerprint of every recorded response.

The corpus fixtures are 342 MB and stay out of the repository, so the study's
numbers rest on recordings only one machine holds. This manifest is the part
that fits: one row per domain, naming when it was read, what came back, and the
SHA-256 of the robots.txt body.

That is enough for a stranger to check the claim. Fetch a robots.txt today, hash
it the same way, and the hashes either match or the site has changed since. Use
scripts/verify_manifest.py, which does exactly that and applies the same
normalisation.

The hash is taken over the decoded body re-encoded as UTF-8, not over the bytes
on the wire. Recording keeps text, not bytes, so a site served as latin-1 hashes
as its UTF-8 equivalent. The verifier normalises identically, which is why it
exists rather than a line of documentation asking the reader to guess.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from geo_check import fixtures

CORPUS = ROOT / "data" / "corpus.txt"
FIXTURES = ROOT / "tests" / "fixtures" / "corpus"
MANIFEST = ROOT / "data" / "corpus_manifest.csv"

FIELDS = [
    "domain",
    "fetched_at",
    "outcome",
    "robots_url",
    "robots_status",
    "robots_sha256",
    "robots_bytes",
]


def read_corpus(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def digest(text: str) -> tuple[str, int]:
    body = text.encode("utf-8")
    return hashlib.sha256(body).hexdigest(), len(body)


def robots_response(recorded: dict) -> tuple[str, dict] | tuple[None, None]:
    """The recorded /robots.txt, whatever host the redirects landed on."""
    for url, response in recorded["responses"].items():
        if urlsplit(url).path == "/robots.txt":
            return url, response
    return None, None


def row_for(domain: str) -> dict[str, object]:
    recorded = fixtures.load(FIXTURES, domain)
    url, response = robots_response(recorded)
    row = {
        "domain": domain,
        "fetched_at": recorded["fetched_at"],
        "outcome": recorded["outcome"],
        "robots_url": url or "",
        "robots_status": "",
        "robots_sha256": "",
        "robots_bytes": "",
    }
    if response is None:
        # The run aborted before robots.txt was reached. Left empty rather than
        # filled with a zero that would read as an empty file.
        return row
    row["robots_status"] = (
        response["status"] if response["status"] is not None else response["error"] or "error"
    )
    if response["status"] == 200:
        row["robots_sha256"], row["robots_bytes"] = digest(response.get("text") or "")
    return row


def rendered(rows: list[dict[str, object]]) -> str:
    """The manifest as text, so --check can compare it without writing it."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description="Write data/corpus_manifest.csv.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if the committed manifest is not what the fixtures produce.",
    )
    args = parser.parse_args()

    domains = read_corpus(CORPUS)
    missing = [d for d in domains if not fixtures.path_for(FIXTURES, d).exists()]
    if missing:
        print(f"no fixture for {len(missing)} domains, first: {missing[:3]}", file=sys.stderr)
        return 1

    rows = [row_for(domain) for domain in domains]
    wanted = rendered(rows)

    # docs/VALIDATION.md promises this file reproduces byte for byte from the
    # recordings. Nothing checked that until now, and an unchecked promise is
    # what let three other generated files drift.
    if args.check:
        current = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
        if current == wanted:
            print("data/corpus_manifest.csv is current.")
            return 0
        print("data/corpus_manifest.csv does not match the fixtures.", file=sys.stderr)
        return 1

    MANIFEST.write_text(wanted, encoding="utf-8", newline="\n")
    hashed = sum(1 for row in rows if row["robots_sha256"])
    size = MANIFEST.stat().st_size
    print(f"{len(rows)} domains, {hashed} with a hashed robots.txt, {size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
