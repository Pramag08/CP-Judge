# C10 — recoverable private version publication

**COMPLETE — local PASS, one agent.** Owner + current import scope + explicit
`problems.publish` capability, current successful attempt and CSRF-protected POST
are required. The native import page publishes/resumes immutable private versions;
it never assigns a contest problem, changes visibility or enables submissions.

Reused C08/C09 sanitization, B04/B05 mapping, `verify_install` and the immutable
`site_problem` installer. Additive migration0006 records a unique version/code and
frozen manifest per import/attempt. Publication commits an intent, privately stages
and fsyncs verified files, installs by no-replace rename, then atomically creates
the native private/manually-managed Problem, publication state and audit. Retries
verify/reuse bytes; older versions are never overwritten. Exact case/group mapping,
checker standard and seconds/KiB limits are checked; extra execution fields rejected.
Submission languages remain empty; HTTP and `Submission.judge` both deny admission.

Only the publication POST releases C17's outer request transaction after admission;
session generation/hash, account and scope are rechecked under account locks at
intent/finalization. Other routes retain their locking. B06's receipt renderer
and protected PNG/CSS routes use the frozen sanitized presentation.

| Check | Actual result |
| --- | --- |
| Focused tests |25 passed,0 skips:20 C10 +3 C09 +2 existing session regressions; six existing B05 installer tests also passed. |
| Failure/recovery |Disk/fsync and post-rename DB exceptions, pre-rename interruption/partial staging, and actual child exit72 after rename all recovered without replacing old bytes. Native rollback/same-inode retry verified. Concurrent calls produced one version/audit; revoked/replaced sessions could not finalize. |
| Browser |Native UI published24/attempt2 → `pv900000000000000002`; sample/math/image/notices, headers, duplicate/refresh, role/hidden-data and admission checks passed. Screenshot inspected. Earlier private version1 from a failed browser exploration remained usable. |
| Native/files |All installed hashes and native fields agree:0.5s,65536KiB,CPP17 checker,3 active tests/3 points,1 sample. No contest assignment, public flag, languages or submissions. Group fixture independently preserves30/50/20 points and dependency2→1. Migration consistency exit0. |
| Preservation |63 model sets/1776 prior rows preserved, except allowed login/access/session generation and judge liveness. Passwords/IDs/results/keys/visibility unchanged. One native-expired browser contest pointer was restored to baseline. Four container IDs/images/configuration/start times unchanged; only HTTP/Celery reloaded, worker/sandbox untouched. |

[Browser](browser.json), [native/file agreement](native-files.json),
[tests/pins/backup/source hashes](checks.json), [preservation](preservation.json),
[restored browser context](browser-context.json), [containers](containers-preserved.json),
[exact subprocess commands/exits](commands.json). Raw logs, readable private backup,
staging receipts and screenshots remain ignored under `build/phase-c-c10-1/`.

Recovery: retry the same publication POST, or run
`python manage.py recover_publications VERSION_ID` inside the site container;
both reauthorize the owner/current attempt and refuse changed frozen inputs.
Abandoned partial staging stays private; automatic garbage collection is not added.
Process-loss recovery is tested; hardware power loss, container recreation and
backup restore are not. No worker files/advertisement/readiness receipt or judging
probe was installed or exercised. The unchanged **111MiB original archive exceeds
32MiB upload/128MiB conversion limits**; C10 uses smaller synthetic fixtures and
claims **no full-package verification**. C09's real-statement fixture is not such proof.

Final command executions (repository root, each exit0):

```sh
sg docker -c 'python3 -B deploy/phase-c/c10.py backup'
sg docker -c 'python3 -B deploy/phase-c/c10.py stage'
sg docker -c 'python3 -B deploy/phase-c/c10.py migration'
sg docker -c 'python3 -B deploy/phase-c/c10.py tests'
python3 -B -m unittest discover -s tests -p test_site_problem_install.py -v
sg docker -c 'python3 -B deploy/phase-c/c10.py activate'
sg docker -c 'python3 -B deploy/phase-c/c10.py grant-fixture'
sg docker -c 'python3 -B deploy/phase-c/c10.py browser'
sg docker -c 'python3 -B deploy/phase-c/c10.py verify-publication'
sg docker -c 'python3 -B deploy/phase-c/c10.py restore-browser-context'
sg docker -c 'python3 -B deploy/phase-c/c10.py preserve'
git diff --check
```

Backup is one-time/guarded; reuse evidence. Scope grant targets only the existing
C1LIVEA/c1livea fixture. Failed driver syntax, migration ownership, premature test
runs, CSRF harness setup/encoding, outer-transaction integration and initial
preservation attempts are retained, not counted as passes. First browser attempt
created version1 before failing its duplicate assertion; it was preserved.
**Next: C11 only on request. Stopped before C11 readiness and C13 judging probes.**
No commit or push.
