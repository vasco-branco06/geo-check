# plan.md

Living state of the project. Update at the end of every session. Keep it short.
Decisions live in `CLAUDE.md`, progress lives here.

Last updated: 2026-09-06. Shipped: 0.4.0, on PyPI and the GitHub
Marketplace. Every phase closed. One item open, at the bottom.

## Phase 0, decisions. DONE

Scope, name, rubric, buckets, output format and testing strategy are closed and
recorded in `CLAUDE.md`. Repository scaffold created.

## Phase 1, robots.txt and the Access score. DONE

Goal: `geo-check example.com` reads robots.txt, classifies every agent into its
bucket, and prints an Access score with a letter grade.

- [x] `fetch.py`: HTTP layer with timeouts, retries, a polite identifying
      user-agent, and a typed failure reason on every error path
- [x] `robots.py`: protego wrapper, fake robots.txt detection, per-agent verdict
- [x] `checks/access_*.py`: one file per Access criterion
- [x] `scoring.py`: already written, verify against the rubric
- [x] `cli.py`: minimal command, text output only
- [x] Manual run against 5 sites known by hand, including one that blocks
      everything and one with no robots.txt

Done when: the Access score is correct on those 5 sites and every failure path
returns a reason instead of a traceback.

## Phase 2, page sampling and the Readability score. DONE

Goal: sample 5 pages from the sitemap and score Readability.

- [x] Sitemap discovery, robots.txt directive first, then `/sitemap.xml`
- [x] Sitemap index handling, one nesting level, capped at 5 nested fetches
      chosen by hash so a site that names its sitemaps by month is not sampled
      entirely from January
- [x] Deterministic sampling, ordered by `sha256(url)`, settled before a single
      request goes out
- [x] `checks/readability_*.py`: one file per criterion, eight of eight
- [x] JavaScript heuristic with thresholds measured across 22 live pages,
      recorded in `data/js_calibration.csv` and reproducible with
      `scripts/calibrate_js_threshold.py`
- [x] `llms.txt` fetched, with the same body over header rule as robots.txt
- [x] robots.txt is honoured for the tool's own user agent when sampling
      pages. The homepage is still always fetched, because without it there is
      nothing to report at all
- [x] Manual run: example.com (Access 90 A, Readability 22 F), observador.pt
      (75.33 B / 75.73 B), sapo.pt (48.67 D / 83.33 B), reddit.com (10 F /
      4.5 F), eco.sapo.pt (100 A / 79.63 B), excalidraw.com (100 A / 32 F, the
      single page application)
- [x] 96 tests, offline, under a second

Done when: Readability is correct on the same 5 sites plus one known
JavaScript-heavy single page application. Met. excalidraw.com scoring 100 on
Access and 32 on Readability is the case that shows why the two scores are
never averaged.

## Phase 3, output and fixes. DONE

- [x] JSON schema, versioned with a `schema_version` field
- [x] Markdown report generated from the JSON
- [x] Terminal text generated from the same JSON, so the three outputs cannot
      disagree about one run
- [x] Remediation templates, including exact robots.txt lines to add
- [x] One merged robots.txt block, so a site blocking both citation and user
      fetch crawlers gets a single thing to paste rather than two overlapping
      groups. Agents documented as ignoring robots.txt are left out of it
- [x] `--json` and `--output` flags write files
- [x] 109 tests, offline, under a second

Done when: a person who has never seen the tool can read the markdown report and
know what to change. Met. The report opens with what to change and closes with
what the tool cannot see.

## Phase 4, corpus and tests. DONE

- [x] `data/corpus.txt`, extended to 906 on 2026-08-31, every one
      checked to resolve before
      it went in. Where a category had more survivors than its target the trim
      was made by ordering on sha256 of the domain, and the 55 candidates that
      did not make the cut are listed at the bottom of the file
- [x] `build_site` takes a fetcher, so the suite replays recorded responses
- [x] `geo_check/fixtures.py` records and replays. A URL the fixture does not
      hold returns a failure with that reason rather than an invented 404
- [x] `scripts/refresh_fixtures.py` records and writes the outcome report
- [x] `data/golden_30.yaml`, 30 hard sites, every expectation traced by hand to
      the group that produced it
- [x] `tests/test_golden.py`, 33 assertions, 100 percent
- [x] `tests/test_robustness.py`, replays the corpus when it is recorded locally
      and skips when it is not
- [x] `data/robustness_report.json`, the per domain outcome

Two decisions taken here and recorded in `CLAUDE.md`, both with measurement
behind them.

Only the golden set ships in the repository, at 8 MB. The 500 site corpus would
be 208 MB, and truncating the pages was tested and rejected, because at a 300 KB
cap 6 of 12 domains moved their Readability score.

Completing means the tool handled the site, not that the site answered. About a
fifth of the corpus sits behind a bot manager that refuses a browser just as
readily.

One bug found, and it is the reason the golden set exists. protego matches user
agents by substring, so Wikipedia's group named `Fetch` captured
`Meta-ExternalFetcher`, and any site with `User-agent: bot` would have blocked
six citation crawlers in one line. Group selection moved into `robots.py`;
protego still answers every path question.

Done when: `pytest` runs offline, in seconds, and passes. Met, 149 tests in
under 12 seconds with no network.

## Phase 5, documentation. DONE

- [x] Renamed to `geo-check`. Package, command, skill and every reference. The
      reasoning is in `CLAUDE.md`
- [x] README rewritten, with a real run against nytimes.com near the top. That
      example was chosen deliberately: the New York Times
      configuration is deliberate and widely reported, so it demonstrates the
      tool reading a real setup correctly without making a smaller company the
      poster child for what is broken
- [x] `docs/RUBRIC.md`, the full rubric with the reasoning, including why
      training crawlers are worth zero and the two known weaknesses stated
      rather than hidden
- [x] `SKILL.md` finalised, with the things to get right when reporting
- [x] One line install verified in a clean virtual environment from a built
      wheel, under the new name

Done when: the floor is met. One line install that works first time, README with
the output near the top, MIT licence, and the tool not crashing on the first site
someone tries. Met.

## Phase 6, validation and launch. DONE

- [x] Ran the tool across the corpus, now 500 sites, and collected the numbers
      (`scripts/run_study.py`, aggregate in `data/study.json`, untracked)
- [x] Wrote `docs/VALIDATION.md`, the evidence that the tool works, and linked it
      from the README
- [ ] Publish the analysis. Not done and not for me to do. Publishing is outward
      facing and irreversible, so it stays with the maintainer.

**The analysis of what the 500 sites revealed about the web is held back
deliberately.** It is the maintainer's article and it is not written down here,
in `docs/`, in the README or in `data/study.json`, which is regenerated locally
and gitignored for exactly that reason.

This is a standing instruction, not a one time edit. A later session that runs
`scripts/run_study.py`, reads the numbers and writes them into the repository
would undo the decision without knowing there was one. Inside the repository the
500 site run has one job: proving the tool handles real input and gives correct
answers. What the run says about anyone's website belongs to the article.

What the repository claimed at the end of this phase, when the corpus was 500:
408 scored, 92 aborted with a logged reason, zero crashes, 9600 verdicts at 100
percent agreement with an independent reader, 182 block verdicts traced by hand,
and the three parser defects the validation found in this tool. Phase 7 doubled
the corpus and every one of those figures moved; `docs/VALIDATION.md` carries the
current ones.

Hardened 2026-08-30, so the evidence survives a stranger checking it.

- [x] `data/corpus_manifest.csv`, 500 rows, 68 KB, the SHA-256 of every
      `robots.txt` as it was read. Built by `scripts/build_manifest.py`, checked
      against the live web by `scripts/verify_manifest.py`. All 25 in the
      reproducible sample still matched on the day it was written
- [x] The 92 aborts split by what they mean, 64 deliberate refusals, 20
      unreachable from here, 8 gone. One number read as one thing and the
      unreachable twenty may answer fine for someone else
- [x] `pytest -m slow` run to completion for the first time since the corpus
      doubled: 3 tests, all 500 replayed, and run again after every edit here
- [x] CI simulated from a clean checkout with no corpus fixtures, on 3.11 and
      3.14, through install, lint, test, wheel build and clean install. It had
      never been executed
- [x] Python 3.14 added to the matrix and the classifiers. `requires-python` has
      no upper bound and the maintainer's own environment is 3.14, so the tested
      range did not include the version being used

A five-lens adversarial audit of that commit then found more, and the largest was
not in any file.

- [x] **The git history stated everything the files no longer do.** Five earlier
      commits carried the withheld comparison in their diffs, and one carried the
      article's finding in its message body, which no edit to a working file can
      reach. Every removal was one `git log -p` away. History restarted from a
      single commit; the old history is bundled outside the repository
- [x] **The corpus was still partitioned, by structure.** Removing the printed
      counts left the sections that produced them, one of which was half the file
      on its own. It is now a single flat block ordered by sha256 of the domain,
      with site type in `data/corpus_categories.csv` across nine uneven types
- [x] `scripts/run_study.py` was silently broken by removing the count suffixes it
      parsed. Every domain fell into `unknown`. It reads the category file now and
      fails loudly instead
- [x] Ten documentation figures corrected against the data, including
      `excalidraw.com` at 32 not 30, the block wall share at 13 percent not 7, the
      hand-traced verdicts scoped to the 182 that score rather than implying all
      520, and the `Crawl-delay` bug described against the lines `eventbrite.com`
      actually writes
- [x] Two unsupported claims removed: three sites answering `GPTBot` with 200,
      which rests on data that does not ship, and two universal claims about
      competing tools
- [x] The JavaScript heuristic's fourth client rendered page, which neither cut
      catches, is now stated in `docs/RUBRIC.md` instead of being counted out

Four things were wrong and are fixed. `docs/VALIDATION.md` attributed five of the
seven 429s to Vercel; it is four Vercel, two istio-envoy, one Cloudflare. The
suite was documented at twelve seconds and measures fifteen. The
README called every abort a CDN refusal. And `data/corpus.txt` still
carried the withheld comparison in its structure, with no sentence saying so.
## Phase 7, the corpus doubled and the study redone. DONE

- [x] 406 domains sourced, DNS checked, added to make `data/corpus.txt` 906.
      One side of the corpus is much harder to source than the other, and it
      constrained the run again: the easy candidates resolved at 100 percent and
      the hard ones at 42, a published shop list returned 404 and a brand
      directory showed names without domains. The shortfall was not filled from
      the easy side, which would have skewed the comparison the study exists to
      make
- [x] Categories assigned from the recorded homepage rather than from memory,
      which is what the six percent error rate on the first 500 cost
- [x] Manifest, robustness, accuracy and study regenerated: 906 corpus, 744
      scored, 162 aborted, 21792 verdicts at 100 percent agreement with the
      independent reader, 470 scoring block verdicts across 67 sites, of which
      289 were traced by hand when the scoring buckets held eleven agents
- [x] Every published figure updated across seven documents

**What the larger sample did to the finding.** At 500 sites the two halves of
the corpus differed by six points of readability, which looked publishable. At
906 the difference changed sign and the formal test fell to z = -1.01. It did not
shrink, it reversed, which is what a difference that was never there looks like.
Publishing at 500 would have published a false result in a confident tone. What
the halves are, and what the comparison shows, stays with the maintainer.

## Phase 8, published, and the list caught up with the vendors. DONE

- [x] On PyPI as `geo-check`, published by `.github/workflows/release.yml` over
      OIDC. No token exists on a laptop or in a repository secret, and a tag
      that disagrees with `pyproject.toml` is refused rather than uploaded.
      0.2.0, 0.3.0 and 0.4.0 shipped on 5 and 6 September
- [x] The agent list went from 25 to 32. Meta, Mistral, Amazon, DuckDuckGo and
      You.com each run a citation crawler this project had never heard of, and
      three on demand fetchers from Amazon and Google are documented as ignoring
      robots.txt while Google was represented here as honouring it everywhere.
      `cohere-ai` came out: Cohere now publishes a page saying it runs no
      crawler. Every addition carries the vendor's own documentation URL
- [x] The user fetch bucket stopped counting blocks that do not work, which had
      been written up as a known weakness since the first release. Measured
      first: 53 of 744 scored sites changed and 26 changed letter
- [x] Content signals read and reported, never scored
- [x] Four failure modes that reached the user as a traceback, as silence, or as
      an audit thrown away after it finished

**What measurement caught before it shipped.** Marking all five new citation
crawlers as AI only would have taken the blackout detection, the failure this
tool exists to find, from 18 sites in the corpus to 4. Not because anything
opened up, but because the condition asks for every AI only crawler to be
blocked and nobody blocks one they have never heard of. The flag was narrowed
instead, and the detection held at 18.

**The documentation was wrong where the code was right.** `SKILL.md` named three
fetchers whose blocks do nothing when six do, and the sentence after that list
tells an assistant not to advise changing a rule aimed at them. The tool has
always left all six out of the robots.txt it offers; the file would have made an
assistant override it. A test now fails when `SKILL.md` does not name them all.

**Three files claimed to be generated and were not.** `docs/CRAWLERS.md`, the
terminal image, and then the banner and the social card, all carrying figures
from releases ago. Two now have generators with a `--check` mode, the images are
held to the recording by tests, and CI runs both checks, because a hand edit
passes `pytest` and fails `--check`. CI also runs on Windows now, and prints
coverage without failing on it.

**The accuracy figures were measured against a list that no longer shipped.**
17025 verdicts covered 25 agents while 32 were shipping. Re-run at 21792, still
100 percent agreement with the independent RFC 9309 reader. The hand traced
count says what it covers rather than what would sound better: 289 of 470.

**The same defect had four more places to hide.** A generated page can still
carry a hand written sentence: the line above the first table in
`docs/CRAWLERS.md` counts the fetchers whose blocks do nothing, and the
generator only rewrites the tables. `docs/RUBRIC.md` names four more counts and
is hand written throughout. All were right and none were held to `agents.json`,
so a test now reads both files back against it. The eighteen blackout sites were
worse: three documents quote a figure that came out of `data/study.json`, which
is gitignored by an earlier decision, so no reader could check it and no test
could read it. It is recomputed from the recordings now, and skipped when they
are not on disk. `scripts/build_manifest.py` was the last generator without a
`--check`, against a promise in `docs/VALIDATION.md` that it rebuilds byte for
byte.

**And the byte ceiling was a promise with nothing behind it.** `SECURITY.md`
says a slow drip of a very large body cannot exhaust memory. `MAX_BYTES` was in
`fetch.py` and nothing verified it. The test serves a megabyte in chunks and
counts how many the server was asked for, because a cap applied after reading
everything would satisfy a shorter test and none of the promise.

**Two things were wrong rather than at risk.** The user agent said
`geo-check/0.1` on every request while the package reported 0.4.0 inside every
report it wrote, three releases apart, so the same run told the reader one
version and the site it was auditing another. And the README's own table of
parsing defects said `User-agent: bot` would have blocked six citation crawlers,
when `GPTBot` is a training crawler and it is five. `fetch.py` derives the string
now and a test binds `__version__` to `pyproject.toml`; the crawler count is
counted from `agents.json`.

**The `v0` tag moved by hand and the workflow claimed otherwise.**
`release.yml` has said since the first publish that the major tag moves forward
with every release. Nothing performed it, and it had already drifted seven
commits while serving the Marketplace a `USER_AGENT` with the old account name.
A job does it now, gated on the publish succeeding and on the ref being a tag,
because a `workflow_dispatch` from a branch named `v0.5-prep` strips to `v0`
exactly as `v0.4.0` does. What it guarantees is that `v0` follows the commit
whose wheel reached PyPI. It does not guarantee that commit passed CI, because
`ci.yml` never runs on tags and `needs` does not cross workflows, and that gap is
written down rather than covered by a second sentence nothing performs.

**The test count is gone rather than corrected.** It said 189 against 198
collected, having been reconciled by hand seven tests earlier. A number that
changes on every commit costs either a subprocess in every run or a conftest hook
with subtle ordering, so what the README states now is what does not churn.

**Two tests could not fail.** The entity test pointed at `file:///etc/passwd` and
asserted `root:` did not come back, which passes on Windows however the parser is
configured. An internal entity separates the settings anywhere. `no_network=True`
stays untested on purpose and the docstring says why: with entities unresolved
nothing is fetched, so a test of it would pass either way, and writing one would
report the promise as covered when it is not. `_pause_for`, which carries the
twenty second backoff learned from a whole CDN answering 429, had no test at all.

**And around thirty published figures now recompute.** The abort breakdown, the
agreement rates, the 710 hashed domains, the block and JavaScript calibrations.
All correct, all read from committed files, none of them ever compared to the
prose beside them. These read what ships rather than the recordings, so unlike
the corpus tests they run in CI.

## Open items

- **Rename the working directory** from `geo-audit` to `geo-check`. Breaks the
  virtual environment, which has to be recreated, and Windows holds the current
  directory open while a session is running.

Closed in phase 8: the user fetch bucket counting blocks that do not work, PyPI
publication, and making the repository public.

Closed earlier: the name (`geo-check`), the agent list verification (checked
against vendor documentation in phase 1 and again in phase 8), the corpus (built
and recorded in phase 4), and the JavaScript threshold (measured across 22 pages
in phase 2, recorded in `data/js_calibration.csv`).
