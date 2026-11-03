# C12 remaining acceptance — COMPLETE, local PASS

Existing upload deduplication needed no application fix. Added only focused
acceptance drivers/tests and updated status. Reused passed [C05](../phase-c-c05-1/README.md),
[C07](../phase-c-c07-1/README.md) and [C10](../phase-c-c10-1/README.md)
behavior/evidence; no conversion, publication or judging suite rerun.

| Check actually run | Observed result |
| --- | --- |
| Three native tests, zero skips | PASS: six separate MariaDB connections overlap after six complete archive writes; one canonical row/archive remains. Four overlapping mixed-owner uploads retain exactly two private jobs/archives. Same-owner other-contest rejection cleans its losing archive. Real storage/inserts; only a preflight barrier coordinates overlap. |
| Live HTTP concurrency | PASS: six simultaneous authenticated POSTs using one current browser session return302 to job37; one canonical archive. Native session middleware serializes account admission; the separate-connection test exercises the storage race directly. |
| Actual Chromium published re-upload | PASS: owner downloads existing job24's ZIP, selects it under a different filename in the normal upload form, and returns to job24/attempt2/version `pv900000000000000002`; refresh agrees. Full stored job/version and existing audit rows remain unchanged. |
| Other-owner privacy | PASS: identical published bytes uploaded by the second scoped author create its own job50/attempt0, without a version; owner download agrees. Each owner receives404 for the other's confirmation/download. Concurrent native tests also verify independent owner records and mutual denial. |
| Preservation | PASS:64 model sets/1896 existing non-session rows checked; passwords, prior results and attempt/audit history preserved. All319 prior private import files retain their hashes. Exactly two new owner-bound archives, zero new orphan files. Four container identities/configurations preserved; no service restart. Only normal login/access/generation/liveness changes allowed; ended native contest pointers restored. |

[Browser results](browser.json), [preservation](preservation.json),
[exact subprocess commands/exits](commands.json). Private raw logs, baseline,
race ZIP and screenshot: ignored `build/phase-c-c12-1/`.

Commands run from repository root, final executions each exit0:

```sh
sg docker -c 'python3 -B deploy/phase-c/c12.py snapshot'
sg docker -c 'python3 -B deploy/phase-c/c12.py tests'
sg docker -c 'python3 -B deploy/phase-c/c12.py prepare-isolation-fixture'
sg docker -c 'python3 -B deploy/phase-c/c12.py browser'
sg docker -c 'python3 -B deploy/phase-c/c12.py preserve'
git diff --check
```

All three new Python files also passed `ast.parse` via `python3 -B -`, exit0.
The first browser run passed published re-upload/concurrency then failed waiting
for the second author's upload form: that fixture lacked its own-contest import
grant. Added only that scoped grant/audit and reused the first race ZIP on retry;
the complete browser run then passed. The failed run remains in the exit ledger.
The fixture's previous permissions, credentials, files and historical reports were
preserved; no account provisioning/reset or identity migration. Existing MariaDB
conditional-constraint warning remains unrelated.

This proves the tested local concurrency envelope, not capacity or host-crash
upload-orphan reconciliation. Unchanged32MiB upload/128MiB conversion limits still
exclude the original111MiB archive. No new conversion, publication, worker probe
or actual judging was performed. No schema/dependency change, commit or push.
**Next: C13 only on request; C18/C19 remain pending.**
