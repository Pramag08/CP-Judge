**B08/B09 PASS.** Four genuine native form submissions by the existing ordinary,
authorized participant; worker logs/callbacks, stored results and browser verdicts
agree. CPP23, private `pv000000000000000001`; A03 probe sources and numbered
expectations reused. CE uses minimal invalid syntax because no historical CE probe existed.

| Probe / ID | Expected / worker / stored / browser | Executed cases and numbering | Evidence |
| --- | --- | --- | --- |
| Known wrong / 2 | WA / WA / WA / WA | 103:55 WA,48 AC; first failure1;48/103 | [Result/cases/browser/callbacks](wrong_answer-result.json), [worker](wrong_answer-worker.log) |
| Invalid source / 3 | CE / CE / CE / CE | 0;103 unexecuted,0 passed; no failed-case number | [Result/browser/callback](compile_error-result.json), [worker](compile_error-worker.log) |
| Crash / 4 | RTE / RTE / RTE / RTE | 103 RTE; first failure1;0/103 | [Result/cases/browser/callbacks](runtime-result.json), [worker](runtime-worker.log) |
| Timeout / 5 | TLE / TLE / TLE / TLE | 103 TLE; first failure1;0/103 | [Result/cases/browser/callbacks](timeout-result.json), [worker](timeout-worker.log) |

All309 executed cases match saved expectations, positions1–103, points and native
callback/SQL timing/memory exactly; browser case numbering/status and final score
agree. No SC records occurred; CE's103 unexecuted cases are not passes.
[Preservation](preserve.json): all88 model snapshots checked; exactly4 Submission,
4 Source and309 testcase additions; existing rows/passwords/permissions/limits,
immutable problem bytes, container images and sandbox configuration preserved.
Browser sessions cleaned through the configured backend. No conversion or CLI
judging was rerun; B07's accepted result was reused without resubmission.

Command: `.venv/bin/python -B deploy/site-local/failure_journey.py <action>`;
`snapshot`, `wrong_answer`, `compile_error`, `runtime`, `timeout`, `preserve`
each finished exit0. [Exact subprocess commands/exits and private log paths](commands.json).
Syntax compilation and final `git diff --check` exited0; raw directory is ignored.
Only acceptance drivers changed: reuse B07 browser/collector, handle native form
whitespace trimming, native CE/log labels, combined callback bitmask precedence,
and resume collection from receipts/saved browser output. Initial snapshot and
CE/RTE driver attempts exited1; original submissions were retained, affected
checks reran read-only, and failed/raw compiler/DOM/screenshots remain under
`build/b08-b09-probes-1/`. No application/judge fix or additional audit script.

Limits stayed2s/262144KiB, short-circuitfalse. Actual TLE case CPU times were
3.000496–4.002942s, consistent with historical native overshoot; this verifies TLE
propagation, not a precise2s boundary or Polygon timing parity. One private CPP23
problem only; contest/standings, recovery/load and production remain untested.
No blocker. **Stopped before B10**; no redesign, commit or push.
