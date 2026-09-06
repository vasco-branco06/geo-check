"""The agent list is data, so it gets tested like data."""

import json
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
AGENTS_PATH = Path(__file__).resolve().parents[1] / "src" / "geo_check" / "data" / "agents.json"
AGENTS = json.loads(AGENTS_PATH.read_text(encoding="utf-8"))


def test_every_agent_has_the_required_fields():
    for agent in AGENTS["agents"]:
        assert agent["token"], agent
        assert agent["vendor"], agent
        assert agent["bucket"] in {"citation", "user_fetch", "training"}, agent
        assert agent["obeys_robots"] in {"yes", "no", "disputed"}, agent
        # An entry either points at the vendor's own documentation or admits it
        # cannot. Pointing at something that is not documentation is the one
        # option this file does not allow itself.
        if agent.get("undocumented"):
            assert agent["docs"] is None, agent
        else:
            assert agent["docs"].startswith("http"), agent


def test_tokens_are_unique():
    tokens = [a["token"] for a in AGENTS["agents"]]
    assert len(tokens) == len(set(tokens))


def test_each_bucket_is_populated():
    buckets = {a["bucket"] for a in AGENTS["agents"]}
    assert buckets == {"citation", "user_fetch", "training"}


def test_the_file_ships_inside_the_package():
    """A wheel does not carry files from outside the package directory."""
    from geo_check.robots import load_agents

    assert len(load_agents()) == len(AGENTS["agents"])


def test_nothing_undocumented_carries_a_score():
    """The citation and user fetch buckets are the Access score.

    Deducting points from a real site because of an agent whose existence rests
    on hearsay is the kind of thing this project is supposed to be against. An
    entry with no vendor documentation can be reported, and cannot be scored.
    """
    for agent in AGENTS["agents"]:
        if agent.get("undocumented"):
            assert agent["bucket"] == "training", agent["token"]


def test_the_skill_names_every_block_that_does_not_work():
    """SKILL.md tells an assistant which blocks are decorative, by name.

    It named three when there were six, having missed the two Google fetchers
    and Amazon's, all added with vendor documentation saying they ignore the
    file. The sentence right after that list is an instruction not to advise
    changing a rule aimed at them, so a stale list is not untidy, it is the
    tool giving the advice it exists to prevent.
    """
    said = SKILL.read_text(encoding="utf-8")
    ineffective = [
        a["token"]
        for a in AGENTS["agents"]
        if a["bucket"] == "user_fetch" and a.get("obeys_robots", "yes") != "yes"
    ]

    missing = [t for t in ineffective if t not in said]
    assert not missing, f"SKILL.md does not name {missing} among the blocks that do nothing"


def test_the_skill_counts_them_correctly():
    total = sum(1 for a in AGENTS["agents"] if a["bucket"] == "user_fetch")
    ineffective = sum(
        1
        for a in AGENTS["agents"]
        if a["bucket"] == "user_fetch" and a.get("obeys_robots", "yes") != "yes"
    )
    words = {
        3: "Three",
        4: "Four",
        5: "Five",
        6: "Six",
        7: "Seven",
        8: "Eight",
        9: "Nine",
        10: "Ten",
    }
    wanted = f"{words[ineffective]} of the {words[total].lower()}"
    said = SKILL.read_text(encoding="utf-8")
    assert wanted in said, f"SKILL.md should say {wanted!r}"
