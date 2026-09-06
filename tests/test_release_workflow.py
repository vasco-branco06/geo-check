"""release.yml says the major tag moves forward with every release.

That sentence sat at the top of the file from the first publish and nothing
performed it. `v0` is what README.md hands people and what the Marketplace
serves, and it was moved by hand until once nobody did: it sat seven commits
behind, serving a USER_AGENT carrying an old account name, which was exactly
what the newer commit existed to remove.

What is checked here is that the job exists and is wired so it cannot do the two
things that would make it worse than nothing: move the tag when publishing
failed, or move it to a branch commit. `v0.5-prep` strips to `v0` exactly as
`v0.4.0` does, so the branch guard is the whole difference between a release tag
and a work in progress.

Whether the API call succeeds is not checkable offline and this suite does not
touch the network. The first release after this lands is what proves that half.
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RELEASE = yaml.safe_load(
    (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
)


def test_a_job_moves_the_major_tag():
    # Found by permission rather than by name, so this also fails if someone
    # widens publish instead of adding a job. That was the design considered and
    # rejected: publish holds an OIDC token, an unpinned pip install and a third
    # party upload action, and permissions cannot be scoped to a single step.
    writers = {
        name: job
        for name, job in RELEASE["jobs"].items()
        if (job.get("permissions") or {}).get("contents") == "write"
    }
    assert len(writers) == 1, f"expected one job able to write refs, found {sorted(writers)}"
    name, job = writers.popitem()

    script = "\n".join(step.get("run") or "" for step in job["steps"])
    assert "refs/tags/" in script, f"{name} writes nothing that looks like a tag"

    # Hardcoding v0 keeps working right up to the release where it is wrong.
    assert "GITHUB_REF_NAME" in script, f"{name} does not derive the major from the tag"

    # A version on PyPI is permanent and a tag is not, so the tag follows the
    # upload rather than racing it. A needs without always() keeps success().
    assert "publish" in (job.get("needs") or []), f"{name} can run when publishing failed"

    # workflow_dispatch runs from a branch, and a branch named v0.5-prep strips
    # to v0. Matching the word rather than one spelling, since ref_type == 'tag'
    # and startsWith(github.ref, 'refs/tags/') are both correct.
    assert "tag" in str(job.get("if", "")), f"{name} would move the tag off a branch"
