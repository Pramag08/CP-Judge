# Organizer ZIP ratio default — 2026-11-08

**PASS for the 1200:1 default and preservation checks.** `CPJ_ARCHIVE_LIMITS['ratio']` is 1200 for all organizer uploads. The #69-specific setting was removed; `archive_limits()` and `archive_limits(job69)` return identical limits, as does the HTTP upload boundary. The preflight central-directory scan now checks each entry's declared ratio before allocating `ZipInfo` objects. `extract_zip` applies the same limits to its metadata and streamed-byte checks. Compressed upload 128 MiB, 1024 entries, per-member 128 MiB, total expanded 320 MiB, path/type checks, and conversion worker limits remain unchanged.

The original #69 ZIP (SHA-256 `acad220c9a9cdc6fee7b9162a571de40de5861891f502b92dcfdcb451e42f8a9`) passed under the **new default without a job exception**: 300 entries and 106,749,143 actual expanded bytes. Before and after this read-only extraction, job69 remained succeeded attempt3, version7 remained published with the same digest, and its probe submission41 remained D/AC with 101 stored case rows. No reimport, publication, judge dispatch or Test1 assignment was performed.

`problem.xml` inspection shows #69 is a standard noninteractive batch problem with one testset, 101 tests, no groups or per-test points, a CPP17 testlib checker, a CPP23 main reference, and HTML/PDF/TeX statement assets. Its 12 entries above the previous 100:1 cap are required input/answer files. The existing converter preserves this package's test files, one-point case scoring, 2 s / 524288 KiB limits, checker standard and declared reference standard, as verified by the prior real AC101 run. **Universal noninteractive Polygon compatibility is not established.** The adapter still explicitly rejects multiple testsets, per-test or partial points, unsupported checker types/languages, file I/O/multiple runs and unsupported statement rendering. Accepting any of those without a faithful native mapping would change judging semantics; they remain explicit unsupported features, not silent downgrades.

## Checks

| Command/action | Exit | Result |
| --- | ---: | --- |
| `.venv/bin/python -B -m unittest discover -s tests -p test_archive.py -v` | 0 | 21 tests pass, including preflight >1200 rejection before `ZipInfo`, exact 1200 preflight acceptance, streamed >1200 rejection despite passing metadata, actual member/total byte caps, count/path/type checks. |
| `docker exec cpjudge-b01-site python manage.py test cpjudge.c08_tests.CompatibilityTests.test_organizer_default_ratio_applies_without_job_exception --settings=dmoj.cpj_integration_settings --keepdb --noinput -v 2` | 0 | Upload boundary, default and job-specific extraction all use 1200 with an empty exception map. Existing MariaDB conditional-constraint warning remains. |
| `docker cp` of native settings, archive extractor and focused site test; `python3 -B deploy/phase-c/c13_bundle.py reload` | 0 each | New default and preflight loaded into local HTTP/Celery. No schema migration. |
| `docker exec ... python /tmp/verify_default69.py` | 0 | Exact SHA, no #69 exception, strict full extraction and unchanged published version/AC101 receipt. Temporary extraction removed. |
| `python3 -B deploy/site-local/manage.py status` | 0 | Site, background services and native worker healthy after reload. |
| Read-only `problem.xml` inspection of ignored original ZIP | 0 | Configuration facts above; no package code executed. |

Private ZIP and diagnostic script remain under ignored `build/`. No commit or push. Next task, only if requested, is a separately scoped compatibility expansion for a concrete noninteractive Polygon package or feature, with its declared scoring/checker semantics and real judge proof.
