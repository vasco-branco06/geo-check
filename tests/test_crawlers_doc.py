"""docs/CRAWLERS.md says it is generated from agents.json. This makes that true.

Nothing generated it and nothing compared them, so the page was free to drift
behind the file it claims to be derived from, and it did: the list grew and the
page did not. A document that describes itself as generated and is not is worse
than one admitting it was written by hand, because a reader trusts it more.

What is checked here is the shape, not the prose. Every agent has a row, every
row is an agent, and the counts in the headings are the counts.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "src" / "geo_check" / "data" / "agents.json"
DOC = ROOT / "docs" / "CRAWLERS.md"
README = ROOT / "README.md"
RUBRIC = ROOT / "docs" / "RUBRIC.md"

BUCKET_HEADINGS = {
    "citation": "## Citation crawlers",
    "user_fetch": "## User fetch crawlers",
    "training": "## Training crawlers",
}

# | `Token` | [Vendor](url) | yes | What it does |, and an undocumented entry
# carries its vendor as plain text because there is no source to link to.
ROW = re.compile(r"^\| `([^`]+)` \| ([^|]+?) \| (yes|no|disputed) \|", re.MULTILINE)
LINK = re.compile(r"^\[([^\]]+)\]\(.+\)$")


def vendor_of(cell: str) -> str:
    match = LINK.match(cell.strip())
    return match.group(1) if match else cell.strip()


def agents() -> list[dict]:
    return json.loads(AGENTS.read_text(encoding="utf-8"))["agents"]


def sections() -> dict[str, str]:
    """The markdown under each bucket heading, up to the next heading."""
    body = DOC.read_text(encoding="utf-8")
    out = {}
    for bucket, heading in BUCKET_HEADINGS.items():
        start = body.index(heading)
        after = body.find("\n## ", start + len(heading))
        out[bucket] = body[start : after if after != -1 else len(body)]
    return out


def test_every_agent_has_a_row_and_every_row_is_an_agent():
    by_bucket = sections()
    for bucket, block in by_bucket.items():
        expected = {a["token"] for a in agents() if a["bucket"] == bucket}
        found = {m.group(1) for m in ROW.finditer(block)}
        assert found == expected, (
            f"{bucket}: missing from the doc {sorted(expected - found)}, "
            f"in the doc but not in the list {sorted(found - expected)}"
        )


def test_the_vendor_and_the_robots_answer_match_the_list():
    by_token = {a["token"]: a for a in agents()}
    for block in sections().values():
        for token, vendor, obeys in (m.groups() for m in ROW.finditer(block)):
            agent = by_token[token]
            assert vendor_of(vendor) == agent["vendor"], token
            assert obeys == agent.get("obeys_robots", "yes"), token


def test_the_counts_in_the_headings_are_the_counts():
    for bucket, block in sections().items():
        expected = sum(1 for a in agents() if a["bucket"] == bucket)
        stated = re.search(r"^(\d+) agents", block, re.MULTILINE)
        assert stated, f"{bucket}: no count line under the heading"
        assert int(stated.group(1)) == expected, (
            f"{bucket}: heading says {stated.group(1)}, the list has {expected}"
        )


def test_the_readme_states_the_real_number_of_agents():
    """The README sells the list, so it is the number people quote back.

    It said twenty five for as long as the list had twenty five, and would have
    gone on saying it.
    """
    expected = len(agents())
    stated = re.search(r"^(\d+) user agents", README.read_text(encoding="utf-8"), re.MULTILINE)
    assert stated, "the README no longer states an agent count in the expected form"
    assert int(stated.group(1)) == expected


WORDS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
    13: "thirteen",
}


def counts() -> dict[str, int]:
    by_bucket = {b: 0 for b in BUCKET_HEADINGS}
    ineffective = 0
    for agent in agents():
        by_bucket[agent["bucket"]] += 1
        if agent["bucket"] == "user_fetch" and agent.get("obeys_robots", "yes") != "yes":
            ineffective += 1
    by_bucket["ineffective"] = ineffective
    return by_bucket


def test_the_prose_counts_agree_with_the_list_too():
    """The tables are generated. The sentences around them are not.

    docs/CRAWLERS.md is rewritten by a script, but only between the bucket
    headings, so the sentence above the first table is hand written inside a
    generated page. RUBRIC.md is hand written throughout. Both name numbers that
    come from agents.json and neither recomputes them, which is the failure that
    produced four stale documents in one week.
    """
    n = counts()
    # RUBRIC.md names four training crawlers and then counts the rest.
    named = 4
    wanted = [
        (
            DOC,
            f"{n['ineffective']} of the {n['user_fetch']} on demand fetchers",
        ),
        (RUBRIC, f"`CCBot` and {n['training'] - named} others"),
        (RUBRIC, f"Split evenly across the {n['citation']}."),
        (RUBRIC, f"Split evenly across the {n['user_fetch']},"),
        (
            RUBRIC,
            f"{WORDS[n['citation'] - 1].capitalize()} of {WORDS[n['citation']]} allowed earns",
        ),
    ]
    for path, phrase in wanted:
        body = path.read_text(encoding="utf-8")
        assert phrase in body, f"{path.name} should say {phrase!r}"


# The tokens a group named `bot` would have captured by substring, listed in
# docs/VALIDATION.md and CLAUDE.md. The README counts how many of them are
# citation crawlers, and that count is a property of agents.json, not of prose.
SUBSTRING_VICTIMS = (
    "GPTBot",
    "Googlebot",
    "Bingbot",
    "PerplexityBot",
    "OAI-SearchBot",
    "Claude-SearchBot",
)


def test_the_readme_counts_the_substring_victims_by_bucket():
    """The README said six citation crawlers and `GPTBot` is a training crawler.

    It sat in a table about parsing defects, which is the worst place to keep one.
    Nothing had ever compared that sentence to the buckets it describes.
    """
    bucket = {a["token"]: a["bucket"] for a in agents()}
    missing = [t for t in SUBSTRING_VICTIMS if t not in bucket]
    assert not missing, f"agents.json no longer carries {missing}"

    citation = sum(1 for t in SUBSTRING_VICTIMS if bucket[t] == "citation")
    phrase = f"{WORDS[citation]} citation crawlers"
    body = README.read_text(encoding="utf-8")
    assert phrase in body, f"README.md should say {phrase!r}"
