# C06 — strict extraction service integration

**PASS for C06's local service acceptance.** Reused `compat.archive.extract_zip`
and the pinned converter's existing Polygon metadata reader/target checks. The
missing integration was an extraction-only boundary: `imports.extracted_upload`
now authorizes an owned stored ZIP, verifies its digest and extracts to a fresh
mode0700 attempt directory outside static/media. It validates metadata without
calling the conversion writer. Context exit removes only that attempt directory,
on success or failure. Original ZIPs, other jobs and upload records remain intact.
The dormant conversion service now reuses this boundary; no queue was enabled.

Errors are returned as safe `ValidationError` messages: fixed archive rejection
reasons or an actionable Polygon checklist, without internal paths. The existing
conversion-service error persistence also uses this sanitizer. HTTP upload still
performs only its C05 preflight; it does not call extraction.

Actual checks (final runs exit0; earlier failures retained in [commands.json](commands.json)):

| Check | Observed result |
| --- | --- |
| Existing focused archive suite, with two missing checks added | **18 passed**. Traversal/absolute paths, symlinks/devices/FIFOs, duplicate/case/Unicode/path-prefix collisions, directory limits, bombs, actual member/aggregate/ratio limits despite dishonest metadata; unsupported encryption/compression/multidisk/ZIP64. |
| Existing converter regressions | **6 passed**, including unsupported Polygon policies/scoring/checkers, missing files and XML entity rejection. These are isolated conversion regressions, not live conversion or judging. |
| Native database service/regression suite | **19 passed**: three new extraction-service tests, eight existing C05 boundary tests and eight affected upload/conversion-core regressions. Supported stored Polygon fixture extracted and validated with conversion blocked; only trusted Git pin checks invoked by metadata loading. Checker/solution/generator/validator/package scripts were never executed. |
| Existing actual C05 website upload → extraction service | **PASS** ([receipt](live-service.json)). The live uploaded ZIP reached the strict extractor once, then safely failed Polygon validation because that C05 fixture contains no problem.xml. Digest, upload record, other files and directory inventory were unchanged; no staging residue. |

No new HTTP extraction action or browser flow was added or tested. Supported
package success and malicious rejection are service-level tests against the
isolated MariaDB test database. The live check used the existing website-uploaded
record through an operator invocation, rather than claiming browser extraction.

Reproduce from repository root (Docker commands require existing project access):

```sh
PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -B -m unittest discover -s tests -p test_archive.py -v
PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -B -m unittest discover -s tests -p test_conversion.py -v
sg docker -c 'python3 -B deploy/phase-c/c06.py stage'
sg docker -c 'python3 -B deploy/phase-c/c06.py tests'
sg docker -c 'python3 -B deploy/phase-c/c06.py live'
git diff --check
```

Private logs are under ignored `build/phase-c-c06-1/`. The service operator supplies
`PCC_ROOT=/tmp/cpj-pcc` in the site container; source pin verification is mandatory.
The live diagnostic uses a process-local Git trust setting for this known checkout
because its owner differs from the root-owned private upload. No global Git or
host security setting changed. A future C07 worker needs this trusted dependency
configuration; it has not been enabled.

No migrations, data changes, service restart, worker/sandbox changes, commit or
push. Temporary service staging cleanup was tested; process crashes, aggregate
storage quotas and durable asynchronous recovery remain future work. Stop before
C07, publication and Phase D.
