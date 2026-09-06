"""What the tool does when the input or the destination is wrong.

Each of these was found by running the tool rather than by reading it, and
each one reached the user as a traceback, as silence, or as lost work. They are
grouped because they share a shape: the audit itself was never the problem.
"""

import argparse
import socket

import httpx
import pytest

from geo_check.cli import _at_least_one, _ready
from geo_check.fetch import _name_does_not_resolve, fetch


def test_a_colon_in_the_domain_is_reported_and_not_raised():
    # httpx.InvalidURL inherits from Exception rather than from HTTPError, so
    # it used to walk past every except clause and out of the process.
    result = fetch("https://site:example.com")

    assert result.status is None
    assert result.error == "invalid_url"


def test_a_name_that_does_not_resolve_is_recognised_through_the_chain():
    # httpx wraps the original, so the gaierror is never the exception caught.
    wrapped = httpx.ConnectError("failed")
    wrapped.__cause__ = socket.gaierror(11001, "getaddrinfo failed")

    assert _name_does_not_resolve(wrapped) is True


def test_an_ordinary_transport_failure_is_still_worth_retrying():
    assert _name_does_not_resolve(httpx.ConnectError("connection refused")) is False
    assert _name_does_not_resolve(httpx.ReadError("reset")) is False


def test_a_missing_directory_is_created_rather_than_thrown_at_the_user(tmp_path):
    # The run is finished by the time these are written. A missing directory
    # used to discard the whole audit after printing it.
    target = tmp_path / "does" / "not" / "exist" / "report.json"

    _ready(target).write_text("{}", encoding="utf-8")

    assert target.read_text(encoding="utf-8") == "{}"


def test_fewer_than_one_page_is_refused_instead_of_quietly_becoming_one():
    assert _at_least_one("5") == 5
    assert _at_least_one("1") == 1
    for refused in ("0", "-5"):
        with pytest.raises(argparse.ArgumentTypeError):
            _at_least_one(refused)


def test_a_body_bigger_than_the_ceiling_stops_being_read(monkeypatch):
    """SECURITY.md promises a byte ceiling and nothing checked it.

    The promise is not that the text comes back short. It is that the read stops.
    A site dripping a very large body must not be able to fill memory while the
    tool waits politely for an end that never arrives, so this counts the chunks
    the server was actually asked for.
    """
    monkeypatch.setattr("geo_check.fetch.MAX_BYTES", 1000)
    served = 0

    def body():
        nonlocal served
        for _ in range(10_000):
            served += 1
            yield b"x" * 100

    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=body()))
    with httpx.Client(transport=transport) as client:
        result = fetch("https://drip.example", client=client)

    assert result.truncated is True
    assert 1000 <= len(result.text) < 2000, len(result.text)
    assert served < 50, f"the whole megabyte was pulled before the cap applied ({served})"
