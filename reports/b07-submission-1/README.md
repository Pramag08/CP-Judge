# B07 — first actual browser-to-worker submission

**PASS — submission1, AC on all103 cases, displayed103/103.**
[Native stored result](result.json), [all actual cases](cases.json),
[browser receipt/result](browser-20261029T115745767981Z.json),
[actual native request/callback trace](native-trace.json),
[sanitized worker log](native-worker-cases.log), [independent review](review.json),
[commands/exits](commands.json), [final audit](evidence-audit.json).

- Problem: http://127.0.0.1:8000/problem/pv000000000000000001
- Submission: http://127.0.0.1:8000/submission/1
- Worker: native authenticated `cpjudge-local-worker`; language **CPP23**.
- Observed actual request: **2.0seconds,262144KiB**, short-circuit false.
- Stored/native callback cases: **103 AC**, each1/1; total **103/103**.
- Participant's native status and My Submissions pages agree: **AC / Accepted**,
  C++23,103/103. Actual screenshots were visually inspected and remain private.

## Genuine execution path and limit proof

B06 completed and was independently reviewed before the separate B07 snapshot.
A fresh Chromium context used the existing ordinary participant's native login
form and scoped native tester access to this private problem. It opened the native
submission page, selected **GNU C++23** (Language19), waited for the native language
template response, filled the real Ace editor with the package's `main` reference
(declared g++23), and clicked the native Submit button. The actual native form POST
and redirect to submission1 were observed. No API/ORM submission creation, CLI
judging, mocked response or database verdict update was substituted.

Native HTML form encoding changes LF to CRLF (2814 source bytes become2916 posted
bytes). The original reference canonical SHA256 is
`09939d650a08b95aa4500e8b026bbbe9cad1edd3b8dfce2e8fd24587e7cd0042`;
the raw posted/stored/sent source SHA256 is
`941da5783b456b47e221955bc1e462ac4496c49ad1131a0048996ae78b7d1fa7`.
Both fingerprints are retained: canonical source exactly matches the package,
and raw source is identical from real POST through database and native bridge send.
No reference algorithm or compiler standard was edited.

A small **passive observation overlay** in the selected native JudgeHandler calls
the original send and original packet handler first, then writes only allowlisted
request/callback fields and source hashes to a mode0600 trace. No packet, scheduling,
limit, status, case or result is altered. Before loading it, the local helpers
stopped only the idle worker/B02 services with existing no-in-progress guards;
DB/Redis/web were preserved. Normal manager start loaded the observer and native
worker reauthenticated. Selected source/image pins remain unchanged with this
explicit diagnostic delta. [Observer identity](observation.json), implementation
`deploy/site-local/bridge_observe.py`; no invented DMOJ protocol fields.

The **actually sent** submission-request for ID1 carried the expected native code,
CPP23, time-limit2.0, memory-limit262144 and short-circuitfalse. Native worker source
at the pinned image converts these exact packet fields to the Submission/Problem
execution budgets; they are not assumed to come from init.yml. No LanguageLimit
override or pretests/contest flag changed the budget. This establishes effective
configured per-case limits, not a calibrated TLE-boundary or Polygon timing proof.

Worker logs show Start grading code/1, Accept submission1,103 sequential explicit
Test case AC lines and Done grading. Actual worker callbacks contain positions1…103,
status bitmask0 and1/1 scores; every callback's timing/memory/points matches the
corresponding stored row exactly. Native stored status is D/resultAC/judged_on the
real worker, with no missing, skipped or fabricated cases. Sum of case CPU time:
1.931150043seconds; max single-case0.02826624seconds; peak10004KiB. These measurements
are one probe, not a load benchmark or precise compiler/platform parity claim.

The native compiler returned **3 warnings** (10 retained message lines); the
submission still genuinely completed AC. Raw compiler text may contain reference
source excerpts and remains private. `compiler_message_sha256` hashes native SQL
text; subprocess collection normalizes
CRLF to LF. [Encoding verification](compiler-message-encoding.json) records both
hashes and verifies exact newline-only equivalence. No warning was silenced
and no warning-free compilation is claimed. Raw judge logs, reference source,
browser DOM/screenshots and cookies remain under ignored build/b07-submission-1/;
public evidence contains only sanitized diagnostics/results/hashes.

## Commands, preservation and boundaries

Final relevant commands from repository root, all exit0:

```sh
.venv/bin/python -B deploy/site-local/problem_journey.py snapshot-submit
.venv/bin/python -B deploy/site-local/problem_journey.py instrument
.venv/bin/python -B deploy/site-local/problem_journey.py submit
.venv/bin/python -B deploy/site-local/problem_journey.py results
.venv/bin/python -B deploy/site-local/problem_journey.py preserve-submit
env CPJ_PROBLEM_REPORT=/home/pramag/Documents/CP-Judge/reports/b07-submission-1 .venv/bin/python -B deploy/site-local/problem_install.py privacy
```

Exactly one real Submission and Source plus103 testcase rows were added by native
browser/worker code. The precise88-model baseline confirms existing passwords,
accounts, roles, statement, limits and other domain data preserved, allowing only
normal native login/access and AC problem-statistics changes. New browser sessions
were removed through the configured cached_db backend. All21 immutable problem
files and worker config/key/image/compiler/sandbox settings remain unchanged.
The focused exact-source privacy check was repeated after the scoped tester grant:
696 anonymous/participant requests denied all private test/checker/reference/static
paths, with fresh B07 evidence. Its temporary session was deleted from DB and cache;
final preservation still shows exactly the expected1/1/103 native additions.

Failed browser setup attempts are retained: readiness predicate accidentally
returned an unbound Ace function; native language-template AJAX then cleared the
editor before click. Native inspection confirmed zero submissions after those
failures. Waiting for the actual template response and native AJAX completion fixed
the driver; the final run asserted both Ace and the genuine textarea held the
reference before clicking. No application UI or validation bypass was introduced.
The first worker-log summary selector missed native colon/code-ID formatting;
raw logs were retained and the corrected read-only collector verified all103 lines.
Read-only results collection repeats did **not** resubmit/rejudge the program.

Independent review covers source/configuration and actual saved execution evidence,
including original reference hash and callback/SQL/browser/worker agreement; reviewer
did not submit or rerun judging. No B07 blocker. B08 failure verdict probes, contest
standings, A11 publication/readiness/version-pool enforcement, timing boundaries,
load/recovery and production deployment remain untested. Existing legacy Gravatar
decoration is blocked by the local-only browser policy; broader offline/CORS/replay
and development warning limitations remain as previously recorded.

Next: **B08 only on request**. No intentional wrong-answer/CE probes, contest,
redesign, learning document, commit or push.
