# B05 — private gaming-grid installation

**PASS for installation/advertisement/privacy checks; judging NOT TESTED.**
[B04 mapping and review](../b04-installation-1/README.md) completed first.
[Commands/exits](commands.json), [operator tests](unit-tests.json),
[independent review](review.json), [final evidence audit](evidence-audit.json).

Installed display problem **gaming-grid**, operator revision **1**, native
Problem/code **`pv000000000000000001`**, PK1. Source package SHA256:
`260abce9770f2c88cf8c93271cbfcbd6cea3f028c6eda536ad16256731d8a769`.
Canonical deployment manifest SHA256:
`7e7b7ec333912da774b066e821eae4c2cb9cb9426ea3417320352d128b5dcf90`.
Full individual-file/case manifests, private data and installation registry stay
under ignored build/, not in public reports or Git.

## Repeatable operator procedure

Existing prerequisites: B01/B02/B03 local deployment, private gaming-grid.zip,
the byte-verified A02 conversion at
`build/a02-converter-1/pipeline/converted-3/`, the converter .venv and reviewed B04
mapping. The temporary PCC/judge source checkouts are absent; reuse the completed
conversion after fresh package checks, without reinstalling dependencies or
reconverting unrelated fixtures. Converter/worker/site/image/compiler pins remain
unchanged; no new compiler/checker/reference execution occurred.

From repository root, with the existing local services running:

```sh
# For a new operator run, preserve data before installation; refuses old snapshot:
.venv/bin/python -B deploy/site-local/problem_install.py snapshot
.venv/bin/python -B deploy/site-local/problem_install.py install
.venv/bin/python -B deploy/site-local/problem_install.py verify
.venv/bin/python -B deploy/site-local/problem_install.py privacy
.venv/bin/python -B deploy/site-local/problem_install.py cleanup-sessions
# Restore only diagnostic participant access-time activity when verifying exact
# preservation against this run's recorded snapshot:
.venv/bin/python -B deploy/site-local/problem_install.py restore-diagnostic-access
.venv/bin/python -B deploy/site-local/problem_install.py preserve
```

For the already-installed revision, repeat only `install` and `verify`; do not
replace the initial snapshot. This is a bounded current-deployment operator tool,
not an author upload interface or general import service. A different revision
requires a new reviewed mapping; `--revision` must match that mapping. Preserve
the ignored registry; loss of it causes existing code/path adoption to be refused.

The installer checks B04 review hashes and independently verifies source bytes.
It binds the full manifest (package/converter pin, files/sizes/hashes, title,
category and frozen native metadata) in a private mode0600 registry. It stages
privately on the same filesystem, verifies again, changes files/directories to
0444/0555, and uses Linux `renameat2(RENAME_NOREPLACE)` for atomic installation.
Symlinks, special files, modified staging, conflicting existing directories and
unregistered code/path adoption are refused. The manifest itself stays outside
the worker data directory.

Existing worker mount `/problems` already maps
`build/b03-worker-1/problems/` read-only; no mount, image, compiler, key or worker
configuration changed. Data lives at `/problems/<native-code>/`.
The host worker-data parent is0700 (worker UID equals operator UID), so only that
user can traverse the0444/0555 immutable data from the host.
Native Problem metadata is installed transactionally, with the required `localpolygon`
category; no ProblemData/ProblemTestCase compiler or reference source is installed.
Original checker/reference language standards and attribution remain intact.

An interruption can leave an immutable private directory before database creation;
the matching registry allows safe retry. It does not expose/publish a half-installed
problem. Conflicting metadata/LanguageLimits fail rather than being overwritten.
No cross-filesystem or distributed publication transaction is claimed.

## Observed results

- First installation created one directory and one native Problem. Repeated
  installation retained PK1/code/full digest and reported both create flags false.
  All21 files were unchanged. Six focused operator tests passed, including stale
  staging, different bytes under the same code, symlink input/parent rejection,
  immutable inode/mtime on repeat, and metadata-sensitive full digests.
- All **103 source input/output pairs** match the worker's **206 archive entries**
  in original order. All21 deployed file sizes/hashes match the converted source;
  checker.cpp/testlib.h, one sample pair and all15 statement/support assets match
  the original package. Sample1 remains an active judged case. Original reference
  source remains only in the private source package, not the deployment.
- Source limits **2000ms/268435456bytes**, installed init/site values
  **2.0seconds/262144KiB**, and B04 expected bridge request values agree.
  Site allowed languages are exactly **CPP23**, with no LanguageLimit overrides;
  checker remains **bridged/testlib CPP23**. Existing CPP23 Language row is unchanged.
  Raw103 one-point cases and standalone Problem.points103/partial=True preserve
  supported converted case scoring; no contest/preset was created.
- Native SIGUSR2 refresh made the actual online `cpjudge-local-worker` advertise
  the exact native code; upstream bridge populated its Judge.problems association.
  No relation, online flag or runtime capability was fabricated. Read-only native
  worker lookup resolves exactly one installed root. No Submission was created,
  no submission-request sent, and no checker/reference run was performed.
- **696 actual HTTP probes** (348 each as anonymous and an authenticated ordinary
  participant) denied downloads:229 native data/init paths per role,105 guessed
  static/media/web paths and14 original checker/header/reference/package paths.
  Anonymous native routes redirect to authentication; participant routes return404;
  static/media routes return404. Positive `/edit/profile/` controls established
  anonymous302 versus participant200. Actual roles and final summaries are in
  `privacy-*.json`; raw session material remains private. This is focused current
  development-route coverage, not a production proxy/security audit.
  Correcting the reference XML XPath was separately checked to yield exactly the
  already-tested source target set: [coverage check](source-route-coverage.json),
  `.venv/bin/python -B reports/b05-problem-1/verify_source_routes.py` exit0.

The problem is **private**, manually managed, has no authors/testers/contest
assignment and a blank statement. No hidden tests, answers, checker/reference
source, sample or statement payload was copied to website source/static/media.
Statement rendering is B06; browser judging begins at B07.

## Preservation, commands and review

All principal commands above finished with exit0 in the final runs. Exact argv,
UTC timestamps, subprocess exits and logs are in commands.json. Read-only `plan`
belongs to the separate B04 report. Operator tests ran:
`.venv/bin/python -B -m unittest discover -s tests -p test_site_problem_install.py -v`
with exit0, six tests. `git diff --check` and the saved-evidence audit are recorded
in evidence-audit.json. No old evidence was overwritten or historical test suite
rerun to claim new judging success.

Private comparison covers88 models including auto-created relation tables.
Pre-existing accounts/passwords/sessions, domain data and worker authentication
match the recorded snapshot. Exactly one row was added to each of Problem,
ProblemGroup, allowed-language relation and native worker/problem relation.
Worker config/key and existing lifecycle sources remain byte-identical. No
password reset, account change, migration or existing problem/submission edit.

HTTP access logging naturally updated the diagnostic participant's last_access;
the verifier caught it, and restored only that field with identity/concurrency
guards. The original snapshot uses DjangoJSONEncoder's **millisecond datetime
precision**: this access timestamp is restored to recorded precision, and original
sub-millisecond precision cannot be asserted. Other non-datetime fields/passwords
are exact. This narrow activity-metadata limitation does not affect installation.
All three owned diagnostic sessions were deleted through the configured cached_db
backend from both DB and cache; existing sessions were untouched.

Retained failed explorations: worker verifier first treated native supported
problem strings as tuples (exit1; corrected); first privacy attempt hit a local
import-scope error (exit1; session removed); initial session cleanup removed only
DB rows (review caught it; backend cleanup then purged all owned keys); first
preservation check caught diagnostic last_access (exit1; restored as above).
Final relevant checks passed; no failed result is treated as a pass.

Independent reviewer inspected configuration/source and saved execution evidence,
also independently compared host-installed pairs/checker/header and manifest;
did not execute submissions or rerun services. No installation blocker.

Remaining: A11 boot-bound readiness/probe receipts, dispatch-time version/pool
enforcement and correction-attempt handling are not implemented; installation and
native advertisement do not prove judging compatibility. Problem remains private
pending later gates. Existing development warnings, browser polling fallback,
volatile replay and idle-only lifecycle limitations remain. Next: **B06 only when
requested**. No author upload, redesign, learning document, commit or push.
