# Test1 latest ZIP rejection — local diagnosis, 2026-11-07

Latest Test1 import is job **69**, attempt 2, still **failed**. The stored archive SHA-256 is `acad220c9a9cdc6fee7b9162a571de40de5861891f502b92dcfdcb451e42f8a9`. The original mode-0600 ZIP remains in private site storage; an unchanged diagnostic copy is under ignored `build/foobar-zip-limit-1/`. This task did not extract, open a ZIP member, run package code, retry conversion, publish, or judge it. Prior job64 remains separate and successful.

The strict extractor's central-directory metadata loop rejected **entry 41**, under `tests/`, at the condition `file_size > max(compress_size, 1) * ratio`. It declares **485,719 expanded bytes / 1,455 compressed bytes = 333.83:1**, against the active **100:1 per-entry compression ratio cap**. The previous message grouped expansion and ratio limits together. The updated stored job69 error and future numeric-only errors now identify entry index, both byte counts, measured ratio and configured cap without exposing private paths.

| Check | Measured | Active limit | Result |
| --- | ---: | ---: | --- |
| ZIP on disk | 43,762,644 bytes (41.735 MiB) | 134,217,728 bytes (128 MiB) | Within |
| Entries | 300 total, 284 files | 1,024 | Within |
| Total expanded (declared) | 106,749,143 bytes (101.804 MiB) | 335,544,320 bytes (320 MiB) | Within |
| Largest entry (declared) | 2,002,015 bytes (1.909 MiB) | 134,217,728 bytes (128 MiB) | Within |
| First failed per-entry ratio | 485,719 / 1,455 = 333.83:1, entry 41 | 100:1 | Rejected |
| Highest per-entry ratio | 600,007 / 608 = 986.85:1, entry 101 | 100:1 | Exceeds |
| Overall member ratio | 106,749,143 / 43,730,806 = 2.44:1 | No overall-ratio cap; expanded total is capped | Context |

Twelve members over 100:1 are all under `tests/`; together they declare 4,123,264 expanded bytes from 6,833 compressed bytes. Central-directory inspection alone does not prove they are all required by `problem.xml` or verify their decompressed bytes. If they are required test data, a **1200:1 per-entry cap** is a bounded candidate: it is 21.6% above the measured 986.85:1 maximum. A read-only check confirms all entries satisfy 1200:1 and the unchanged compressed-size, entry-count, member-size and total-expanded caps. This is a proposal, **not an applied limit change**. Keep path, symlink, encryption, method, duplicate, count, streamed-byte and immutable-package checks. Do not remove tests or change scoring to fit the current cap.

## Checks and disposition

| Command or action | Exit | Observed |
| --- | ---: | --- |
| `git status --short`; read `AGENTS.md`, `PROJECT_STATUS.md`, root plan | 0 | Prior dirty work preserved. |
| Read-only ORM query for Test1 imports and active `CPJ_ARCHIVE_LIMITS`; `sg docker -c 'docker cp cpjudge-b01-site:/app/private-cpj-imports/82c5a7f3faf9ce89ba6975300ca87b525bb811115b871a4b.zip build/foobar-zip-limit-1/upload69.zip'` | 0 | Job69 latest failed; source and copy SHA-256 match; active ratio 100. |
| Python central-directory-only `preflight_directory` and `ZipFile.infolist()` measurement; no member `open`/read | 0 | Values above; first failing check is ratio at entry41, not total expansion, member size or count. |
| Python central-directory-only candidate check with `ArchiveLimits(..., ratio=1200)` | 0 | All declared entries fit candidate and existing other caps; no extraction or conversion proof. |
| `.venv/bin/python -B -m unittest discover -s tests -p test_archive.py -v` | 0 | 18 synthetic archive tests pass, including ratio rejection and existing streamed-byte guards. |
| `.venv/bin/python -B -c` numeric public-error allowlist check; `python3 -B -m py_compile` touched Python files; `git diff --check` | 0 each | Exact 333.83:1 versus 100:1 message accepted; appended private-path text rejected; syntax/whitespace pass. |
| `python3 -B deploy/phase-c/c13_bundle.py reload`; isolated `cpjudge.c08_tests.CompatibilityTests.test_rejection_guidance_is_fixed_actionable_and_does_not_echo_private_text` | 0 each | Idle HTTP/Celery loaded error change; one focused site test passed. |
| Conditional ORM update of only job69's prior generic error, matching ID, hash, failed status and attempt | 0; 1 row | Job remains failed; original archive and attempt unchanged. |
| Chromium authorized GET `/imports/69/` | 0 | Shows Test1 and exact 485719/1455, 333.83:1 versus 100:1; offers corrected ZIP, no Retry. |

No judging, full archive validation, actual decompression or scoring verification was performed for job69. Next task, if the organizer confirms these high-ratio `tests/` entries are required and authorizes the bounded cap, is to apply 1200:1, then retest the unchanged stored ZIP through the normal guarded import path. No commit or push.
