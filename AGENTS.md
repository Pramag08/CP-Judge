# Scope and invariants

- Work only on the authorized task/bundle. Scope covers problem importing and
  real DMOJ contest judging. B01's local stock website/
  database, B02 services, B03 worker registration and B04/B05 private problem
  mapping/installation, B06 rendering, B07 first browser AC and B08/B09 failure
  verdict checks, B10/B11 private contest/standings and B12 restart persistence
  checks are complete. Phase B / M1 is complete for its scoped local proof; do not
  start Phase C without a request. No custom UI,
  lockdown or full contest deployment. Required upstream static builds are allowed
  within an explicitly requested website-baseline task.
- Reuse upstream projects, pin tested versions or commits, and preserve attribution
  and existing work.
- Keep `local-packages/`, extracted private problems, secrets, and raw private judge
  logs out of Git. Store private outputs under ignored `build/` directories.
- Report conversion and judging separately. Never claim a test passed unless it
  actually ran; unavailable executors, skips, and incomplete logs cannot pass.
- Preserve declared checker/reference language standards, limits, and scoring.
  Mark unsupported features explicitly rather than silently downgrading them.
- Do not commit private packages or push changes without explicit authorization.
- Current MVP target: eligible contests; personal email/password, one account per
  canonical email and one active session per account (C18 email-only mode is active;
  fixture addresses are explicitly organizer-assigned development identifiers); scoped participant/author/admin; individual
  Problems/editor/submissions/standings; Polygon imports, entrant management and
  supervised, in-person competitions. D14 problem clarifications are deferred; no
  standalone archive/problemset, practice, editorials, virtual participation or
  announcements in MVP navigation. Google, teams, groups, ratings,
  matchmaking and general announcements are deferred. Current header branding is
  the supplied foobar logo with `foobar` site titles; do not implement a demonstration role switch as auth.
- Approved UI: retain DMOJ horizontal navigation, centered content, compact tables,
  sidebar styling and footer; adapt existing templates, no separate frontend.
  See `docs/contracts/ui-direction.md`. The current user-approved foobar logo
  and title replace the earlier plain-text header; B01 did not implement the eligible homepage.
- Normative contracts live in `docs/contracts/`; reuse pinned native models,
  transport and executors. Do not invent DMOJ protocol fields. Browser state is
  never authoritative for permissions, clocks, results or worker readiness.

## Task and documentation workflow

- Before starting, read `PROJECT_STATUS.md`, this file and the actual implementation
  plan, currently `SecureExam-Implementation-Plan.md` at the repository root. Resolve
  paths against the repository; do not assume proposed directories exist.
- Complete only the requested task. After each task update `PROJECT_STATUS.md`
  and the plan's task status with evidence paths, exact commands/exit statuses,
  observed results, important decisions, blockers, untested features and next task.
- Keep future reporting to one short task summary: changes, checks, results and remaining
  issues. Reuse existing test output; retain detailed logs only when useful for debugging.
  Add audits or verification scripts only for a concrete correctness concern.
- Keep `PROJECT_STATUS.md` concise. Preserve useful unique facts and user-written
  notes when consolidating documentation. Keep private raw evidence under `build/`
  and sanitized reproducible evidence under `reports/`; preserve previous runs.
- Do not create learning documents, lessons, exercises or long Q&A. Learning takes
  place in the user's separate ChatGPT conversation.
- Distinguish inspected historical evidence, conversion checks and actual judging.
  Keep terminal responses brief: task status, evidence/document paths and blockers.
- Resume from the latest completed row/evidence and named next task; inspect Git
  status and relevant contracts/source first. Existing dirty work is intentional.
  Never reset it. Check whether a dependency already passed before running it.
- A09 startup does not prove website/judge integration. Its failed diagnostic is
  retained historically; B01's additive migration fix now passes consistency.
  B01's stock authentication/admin browser proof does not complete B08–B12 or
  custom account/session policies. No Phase A design proves enforcement.
- For authorized parallel work, assign exclusive file ownership. One coordinator
  updates shared status/plan/contracts sequentially; separate service ports/data.
  Do not delegate otherwise. Record source pins, exact commands/exits, observed
  results, decisions, blockers, untested behavior and next task after each task.

## Working commands

Run from repository root. These are recipes, not instructions to repeat checks
that already passed. Use fresh ignored output directories for every new run.

```sh
git status --short
git diff --check
PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -B -m unittest discover -s tests -p test_conversion.py -v
PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -B -m tools.pipeline --output build/new-conversion-run --real local-packages/gaming-grid.zip
.venv/bin/python -B -m tools.verify_install local-packages/gaming-grid.zip build/new-conversion-run/converted-3
```

The converter uses the existing `.venv`; do not install website dependencies there.
Pins are in `dependencies.json`, `requirements-judge.txt` and A09's report locks.
Site source is currently `build/a09-site-1/site`; no `apps/site/` exists. Judge
source is `/tmp/cp-judge-dmoj`; PCC is `/tmp/cp-judge-pcc`. Verify pins/existence
before using temporary checkouts; their availability is not persistent deployment.

- Current B01 local site: `python3 -B deploy/site-local/manage.py start|stop|status`
  (choose one action); localhost:8000. `accounts` prints the ignored private file
  location, not credentials. Start/stop preserve the named dev DB volume. `up`
  refuses existing objects. `verify` is read-only for accounts/schema and preserves
  changed passwords; only explicit `reset-accounts` reapplies a private credential
  file. See `reports/b01-followup-1/README.md` for current asset/verify behavior;
  original B01 reports are historical and must remain unchanged. Production
  hardening warnings remain visible.
- Historical A09 startup/replay: follow `reports/a09-site-1/README.md`, including new
  directory/prefix and exact locked image. Docker here used `sg docker -c '…'`.
  No services from A09 remain. Do not load demo passwords or private env into Git.
- Actual CLI judging: follow `reports/a03-judge-1/README.md`; use the pinned image
  and fresh output. Assert every expected executor/case/score and complete logs.
  Exit zero alone, missing executors and dependency skips cannot pass.
- Source-only A10–A12 probes: commands in each `reports/a*-*/README.md`; they use
  isolated native functions/fixtures, not SQL/ORM, network or a live sandbox.
- Current bundle audit: `python3 -B reports/phase-a-close-1/verify.py --task final`.
  It checks links/dependencies, preserved evidence/source and task status, and
  writes a fresh ignored snapshot; it is not a runtime test. Earlier historical
  doc verifiers encode their old scope and must not be overwritten/reused as
  current acceptance. Use a fresh report/run name if changing this baseline.

Task handoff: ID and authorization boundary; dependency evidence; exclusive allowed
paths; fixed contracts/pins; smallest required change/check; exact command/exits;
observations; untested items/blockers; next task. A later agent must be able to
resume from `PROJECT_STATUS.md` without rerunning historical milestones.

B02 lifecycle: start/stop/status also manage native bridge, Celery and events when
`build/b02-services-1/enabled` exists. See reports/b02-services-1/README.md. Bridge
startup now permits only the privately matched B03 registration and still refuses
unknown judges/in-progress jobs because upstream resets their state. B03 lifecycle
also manages the native worker when `build/b03-worker-1/enabled` exists, starting
it last and stopping it first using native SIGINT cleanup. Use the local manager;
direct bridge stop refuses online judges. See reports/b03-worker-1/README.md.
The worker shares the site's network namespace, disables its implicit API and
retains native submitted-program network denial. B03 verifies idle registration,
executors and reconnect only; never infer successful judging or in-flight recovery.

B04/B05 operator installation: see reports/b04-installation-1/README.md and
reports/b05-problem-1/README.md. Private gaming-grid revision1 is native code
`pv000000000000000001`, full manifest registry under ignored build/b05-problem-1/.
`install`/`verify` in deploy/site-local/problem_install.py safely repeat only the
reviewed revision; do not replace its initial snapshot or reuse a code for changed
bytes. Problem remains private, CPP23-only,2s/262144KiB. B06 adds only a separate
receipt-bound sanitized description/scoped stylesheet and native tester grant;
the operator verifier checks that receipt without altering the original judge
manifest. B07 native browser submission1 is AC on103 cases; this does not complete
publication/readiness/version-pool or contest gates. Diagnostic profile access
timestamp restoration has recorded millisecond precision; other account fields,
passwords and worker configuration were preserved.

B06/B07 current evidence: reports/b06-statement-1/README.md and
reports/b07-submission-1/README.md. Source HTML/CSS/TeX adapter is limited to this
selected statement and rejects unsafe/native alternative math input. Private
assets must stay behind native problem permissions, outside static/media.
The live bridge has a passive, sanitized request/callback observer loaded through
an idle guarded restart; it never changes protocol/results. Raw browser/compiler/
judge evidence and source remain ignored under build/. Submission1's103 actual
AC rows and native display agree;3 compiler warnings retained. No standings, timing-boundary, recovery or production claim. B08/B09 failure
verdicts now pass: reports/b08-b09-probes-1/README.md. Submissions2–5 are WA/CE/RTE/TLE;
309 actual case records agree with worker/callback/SQL/browser. CE executed no
cases. Data/configuration preserved; no application fix or AC rerun at that boundary.

B10/B11 evidence: reports/b10-b11-contest-1/README.md. Private native contest
`b10b11local1`, temporary ordinary `b10tmpa`/`b10tmpb`, submissions6–11. Registered
`cpjudge_icpc_v1` and metadata migration0154 fix the observed stock hidden tiebreaker
and stable-row ordering; native case points/data/limits remain unchanged. Both
entrants1 solved/2161s/shared rank1; CE excluded, later WA ignored. Fixed scorer
source/installer under patches/site/contest-format/ and deploy/site-local/; preserve
the local code delta,203 migrations and private fixture. Browser/SQL/callback checks
and18 focused checks pass; non-tie SQL/1,1,3/replacement checks are constructed, not
extra actual judging. Existing data/configuration preserved.

B12 evidence: reports/b12-restart-1/README.md. Supported full stop/start preserves
completed results (11 existing submissions/927 case rows), credentials, contest and
standings; same containers/DB volume, native worker reconnect, new browser
submission12 AC on103 cases. Both entrants remain1 solved/2161s/shared rank1 after
this later AC. Phase B / M1 COMPLETE for scoped gates. No in-progress jobs were
interrupted: interrupted judging/crash recovery is NOT TESTED. No application fix,
reset, migration or rejudge. Preserve fixture and code delta; Phase C only on request.

C13/C19 and same-version integration evidence remain preserved under
reports/phase-c-c13-identity-1/ and reports/phase-c-integrated-1/. C18 email-only
cutover and Phase C retained local gates now pass: reports/phase-c-c18-cutover-1/README.md.
All original password hashes/IDs/history preserved. Four legacy fixtures received
explicitly user-authorized organizer-assigned development addresses, not verified
mailboxes or real identities. Email-only mode is active; local audited administrator
recovery is documented in the closure report. C14/C15 remain deferred. Phase D,
commit/push and limit changes are not authorized by this closure.
