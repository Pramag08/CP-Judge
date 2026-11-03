# A12 — custom-input Run integration contract

Status: **design complete; execution adapter not implemented or compatibility
tested**. [Inspection evidence](../../reports/a12-run-1/README.md). Custom Run is
separate from official submission/scoring and from the A03 actual CLI judge tests.

## Current scope — deferred, 2 November 2026

The dedicated custom-input Run adapter/UI is **DEFERRED**, not a local website or
release prerequisite. The design below remains historical future implementation
guidance only; “implement” wording does not authorize work now. Preserve completed
C13 known-solution probes and D13 private unranked author submissions, which reuse
the native isolated judge and are distinct from arbitrary participant stdin Run.
E07/E08/G12 are outside the current dependency closure. No new protocol, broker,
runner, quotas or execution infrastructure is required for the minimum journey.

## Actual upstream execution route

At site `604d60cfd764bc708b04ffd75b715a5398b91f8b` and worker
`1245dc4158dbb9e906c4c103e1ea939e012ee79b`:

- `judgeapi.judge_submission()` dispatches an existing native Submission/problem
  to the bridge. Worker `PacketManager._receive_packet()` accepts ordinary
  `submission-request` but has no custom-stdin/run message handler.
- Worker `JudgeWorker._grade_cases()` constructs `Problem(code, limits, meta)` and
  iterates its installed cases. StandardGrader reads case input, executes the
  program, then invokes the checker against expected output. `dmoj-cli submit`
  also requires an installed problem; it is not a custom-input Run endpoint.
- `control.py` offers POST `/update/problems` and GET `/metrics`; it does not
  execute custom input. Do not expose this operator control API to participants.
- The usable lower-level execution building blocks are real APIs:
  `executors.executors[language].Executor(fixed_job_name, source_bytes)` compiles
  using the executor constructor/metaclass; `executor.launch(time=...,
  memory=..., wall_time=..., stdin=PIPE, stdout=PIPE, stderr=PIPE)` returns
  sandboxed `TracedPopen`; `process.communicate(input_bytes, outlimit=...,
  errlimit=...)` feeds stdin and bounds collection. `BaseExecutor.launch` supplies
  syscall/filesystem security, runtime environment and resource controls.
  `BaseExecutor.run_self_test` is an upstream example feeding custom bytes through
  launch/communicate without a Problem or checker.

Implement a small **new dedicated runner adapter** inside a derived pinned judge
runtime image. An authenticated internal job broker invokes that adapter in a
fresh isolated execution environment; it loads only enabled/self-tested executor
classes, constructs the executor directly, feeds the supplied bytes and reports
process facts. It does not instantiate Problem/StandardGrader, load init.yml,
mount problem roots, call a checker, generate expected answers, connect to the
official bridge or create Submission/ContestSubmission rows. Do not install
per-user synthetic problems or overload native `meta` to carry stdin. The new
broker request/result schema below is **our internal contract**, not a supported
DMOJ wire protocol extension. Keep the adapter thin and preserve AGPL notices.

Sources: [site judgeapi](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/judgeapi.py),
[packet](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/packet.py),
[worker](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/judge.py),
[CLI submit](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/commands/submit.py),
[control](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/control.py),
[executor](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/executors/base_executor.py),
[compilation](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/executors/compiled_executor.py),
[standard grader](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/graders/standard.py).

## Isolation and initial bounded policy

These are selected **initial configuration limits to implement and test**, not
measured capacity or proof that arbitrary C++ programs compile within them.
Official problem limits remain unchanged; Run displays its separate limits.

| Resource | Initial Run bound and enforcement |
| --- | --- |
| Languages | CPP23 only initially, exact pinned image/compiler and executor self-test; fail unavailable rather than downgrade |
| Source / stdin | Each 65,536 bytes after UTF-8 encoding; stdin is exactly supplied bytes, including empty input and final newline behavior |
| Execution | 2 seconds CPU, 5 seconds wall, 262,144 KiB memory via launch; supervisor hard deadline as backstop |
| Compilation | `compiler_time_limit=10` seconds CPU, 20 seconds wall supervisor; 64 KiB merged diagnostics, 8 MiB executable size, 1 GiB outer job memory |
| Output | stdout ≤65,536 bytes; stderr ≤16,384 bytes; compiler diagnostics ≤65,536 bytes; bounded serialized result including encoding overhead |
| Files/processes | Read-only image/root; fresh executable tmpfs ≤64 MiB; outer PID limit 64; native executor process restriction retained; no user-configurable extra filesystem/symlinks/args/env/flags |
| Host isolation | Unprivileged account, no network, no socket/database/host-home mounts, no credentials or private problem data; dropped capabilities except tested sandbox-required SYS_PTRACE, no-new-privileges, cgroup CPU/memory/PIDs |
| Cleanup | Hard timeout/cancel kills and reaps compiler/program descendants and removes entire disposable job filesystem; exception paths call executor.cleanup where possible |

Use the existing A03 sandbox controls as the baseline, adapting mounts to contain
only this job; a container alone does not establish sandbox security. Compiler
isolation matters as well as runtime isolation: native compilation has no memory
cap (`memory=0`) and allows compiler subprocesses; the new outer job cgroup and
supervisor must provide missing compile memory/wall/PID bounds. Do not run the
compiler on the web server or mount a Docker socket into it. A trusted operator
runner service starts restricted jobs; participant requests cannot choose the
image, host paths, capabilities or launcher command.

Catch `CompileError` as compilation failure. `OutputLimitExceeded` does not carry
partial output; kill/wait and return `output_limit` with empty streams if no safe
prefix was retained. Do not promise truncated content from the native exception.
If later adding bounded prefix capture, it needs its own tested collector. Render
all compiler/stdout/stderr content as inert escaped text, decode invalid UTF-8 with
replacement and mark this fact; do not interpolate into HTML/terminal control
sequences. Program exit is not AC and there is no expected-output comparison.

Sources: [communicate](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/utils/communicate.py),
[errors](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/error.py),
[historical A03 controls](../../reports/a03-judge-1/sandbox.json).

## Authenticated request, quotas and scheduling

Proposed `POST /api/contests/{contest}/problems/{slot}/runs`: authenticated current
session + CSRF; body language key, source, stdin and account-scoped idempotency key.
Server derives identity, contest access, immutable display version and policy;
client cannot supply worker/version/limit overrides. Request returns 202 with
opaque run ID, server receipt timestamp, state and limits; same key+payload returns
same job, changed payload with same key returns 409. `GET .../runs/{id}` and owner
cancellation enforce the same account/contest/session scope on every request and
event. Deny cross-account enumeration with a uniform not-found response.

Run is allowed to eligible active entrants while contest access is open and to
authorized authors in unranked testing. After contest end, MVP new Runs are closed
alongside contest workspace execution; practice is deferred. A Run accepted before
end may finish within its bounds. Removal/account disabling/session replacement
denies future actions and cancels queued/running jobs and event access. Logging
out never transfers job ownership. Retained results remain private to their owner
only while they retain access; account admins receive operational metadata, not
automatic source/input access.

- Atomic account token bucket: burst 2, refill 1 per 15 seconds; maximum one
  active and one queued Run per account. Same idempotent retry consumes no extra
  token. Return 429 plus Retry-After on quota rejection; rejected work never starts.
- Initial global queue maximum 8 and concurrency 1, with 30-second queue expiry;
  per-account round-robin service, no priority granted by an author view. Reserve
  official executor CPU/memory before enabling Run. If that reservation cannot be
  maintained on the host, reject Run as temporarily unavailable (503).
- Separate Run queue/worker role and capacity counters; native official rejudge
  priorities do not supply Run isolation. On a shared initial host, never start a
  Run while official work is pending; an official arrival cancels a competing Run
  within a 1-second supervisor target, returning `interrupted_for_official_work`.
  Verify this target under G12 before enabling the feature. Separate hardware can
  replace preemption once official capacity is demonstrated independent.
- Worker disconnect, supervisor deadline or unknown completion yields an explicit
  infrastructure failure/expired state, never a contestant runtime verdict or
  fabricated output. No implicit retry after disconnect; the user may start a new
  Run under quotas. Attempt IDs and signed internal job leases reject stale or
  duplicate completion writes.

Queue receipt time is not official submission receipt time. No Run writes to
official attempt counts, contest scores, solved state, penalties or standings.

## Result and retention contract

States: queued → compiling → running → finished; terminal failed/cancelled/expired
can follow any nonterminal state. A terminal record is immutable for its execution
attempt. Response contains run ID, state, outcome (`exited`, `compile_error`,
`runtime_error`, `time_limit`, `memory_limit`, `output_limit`,
`infrastructure_error`, `interrupted_for_official_work`), bounded stdout/stderr or
compile diagnostics, nullable exit code/signal, CPU seconds/wall seconds and peak
KiB **only when actually observed**, encoding/omission flags and timestamps.
Multiple resource flags can be retained; classify limit flags before nonzero exit,
and keep unavailable measurements null. Do not manufacture an official verdict,
test number, expected answer or hidden checker feedback. Do not return source or
stdin in event broadcasts; owner may retrieve their own stored request explicitly.

Raw request, source, input, diagnostics and output are private ignored `build/`
evidence during development; production storage requires the same scoped access,
never public static files or raw worker logs. Delete payloads/results after 24
hours (or earlier user deletion), disposable execution files immediately; retain
only minimal job ID/account, timestamps, policy/image identity and outcome for
7 days for quota/incident auditing. Draft/source autosave is a separate feature.

E07/E08 acceptance must execute actual CPP23 echo/empty-input, compile failure,
runtime failure, CPU/wall/memory/output/compile limits, forbidden filesystem and
network, encoding, disconnect, cancel and cleanup probes. Assert official DB
tables/standings untouched, cross-account/removed/revoked sessions denied and no
private problem mount. G12 then verifies queue/quotas/preemption with official
submissions under the supported load envelope. A12 establishes this bounded
route and contract; those implementation/security/capacity tests have **not run**.
There is no Phase A blocker: the lack of native Run transport is explicit custom
adapter work, with real executor APIs identified rather than an invented packet.
