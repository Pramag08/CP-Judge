# A11 — immutable problem versions and compatible dispatch

Status: design complete; source inspection and isolated native function checks.
Live routing was **NOT TESTED at the A11 boundary**. Evidence and
reproduction: [A11 report](../../reports/a11-dispatch-1/README.md).

## C11 implementation boundary (30 October 2026)

**COMPLETE — local initial-worker readiness PASS**; [one summary and actual
checks](../../reports/phase-c-c11-1/README.md). Existing immutable manifests/codes
and pinned worker are reused. A separate private loopback/HMAC challenge channel
checks fresh installed file hashes, configuration/compiler identities and required
solution/checker executors; it binds to the current authenticated bridge handler
and the native worker supervisor's owned TCP socket. No native protocol fields
are invented. Selection, queued/explicit targets and final send all enforce it;
changed versions/runtimes/disconnects cannot reuse an old receipt. Native QU and
an actionable message survive denial; bounded periodic retry resumes valid jobs.

Actual existing Phase B CPP23 submission16 is AC103/103 after a deliberate expected-
hash mismatch and reconnect; temporary-file/native focused checks cover corruption,
stale receipts and queue races. This does not complete C13's isolated problem probe,
contest publication gates, authoritative rejudge attempts, in-flight recovery,
heterogeneous pools or capacity. C10 versions remain submission-disabled/private.
The future design below retains those unimplemented requirements. Immutability
and a trusted single-host operator remain necessary; this is not hardware attestation.

## C13 restricted probe boundary

[C13 local PASS](../../reports/phase-c-c13-identity-1/README.md): known private
solutions execute through native bridge/worker records without ContestSubmission,
participant routes/lists/polls or publication effects. Current owner/scoped/CSRF
admission and final source/version/runtime bindings, fresh C11 attestation,
quotas/deadline/native sandbox limits apply. Actual CPP17 probes AC3/WA3; the C10
installed version remains private and participant submission-disabled. This does
not supply the integrated same-version import→submission→standings release gate.

## Scoped integrated acceptance boundary

[Same-version integration PASS](../../reports/phase-c-integrated-1/README.md): the
existing immutable version2 and accepted private probe17 now connect to three
actual official native submissions and checked fixed standings. An additive
`ContestVersionAdmission` records the explicit scoped author approval, exact digest,
full accepted probe/runtime and private contest rule snapshot before start. It
permits native language metadata for that approval without rewriting the immutable
manifest/test/checker/statement bytes. Native validation expects exactly the union
of base languages and active verified approvals; arbitrary changes fail closed.
Participant reads/submits require allowlist/entry/current scope; official dispatch
revalidates the matching receipt, version, runtime, source and common-clock window.
C11 fresh worker verification remains mandatory. Probe records never become
ContestSubmissions. Other imported/unreleased versions remain participant-disabled.
This is the minimum private integration path, not general publication/lifecycle UI
or complete Phase D acceptance. C18 email-only cutover now passes separately; see the current closure report.

## Native mapping at the selected pins

Site: `604d60cfd764bc708b04ffd75b715a5398b91f8b`; worker:
`1245dc4158dbb9e906c4c103e1ea939e012ee79b`. Preserve upstream AGPL attribution.

| Boundary | Actual native behavior | Integration consequence |
| --- | --- | --- |
| Website identity | `Problem.code` is unique, 20 characters maximum, lower-case letters/digits; `Submission.problem` and `ContestProblem.problem` are foreign keys | One new native Problem row/code per immutable judge revision; a display identity/contest label can group revisions |
| Dispatch | Site `judge_submission()` sends `submission.problem.code` as `problem-id`; bridge forwards it with source, language, seconds/KiB limits, short-circuit and existing meta | Use that native code as the version selector; no new wire `version`, `hash`, `worker-pool` or `stdin` field |
| Worker lookup | `get_problem_root(code)` locates `<root>/<code>/init.yml`; duplicate codes in roots select first match | Exactly one installed path per code; reject duplicate installations; never reuse a code for different bytes |
| Advertisement | Handshake / `supported-problems` carry `(code, directory mtime)` pairs and executor/version lists | Mtime proves neither data integrity nor checker/compiler capability; do not treat it as a version digest |
| Scheduling | `JudgeList` schedules among globally minimum enabled tier, prioritizes queues and least reported load; `can_judge` tests code, executor key and optional judge name | Native routing is useful but insufficient for digest, checker runtime, CPU class or contest pool approval |
| Limits | Bridge rereads Problem/LanguageLimit at dispatch; worker Problem receives packet limits | Freeze version limits and language overrides; dispatch must match submission snapshot, including rejudges |

Sources: [Problem](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/models/problem.py),
[Submission](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/models/submission.py),
[judgeapi](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/judgeapi.py),
[handler](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/bridge/judge_handler.py),
[scheduler](https://github.com/DMOJ/online-judge/blob/604d60cfd764bc708b04ffd75b715a5398b91f8b/judge/bridge/judge_list.py),
[worker packet](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/packet.py).

## Publication and readiness contract

The following are proposed coordinator records, **not existing native models or
wire fields**: display problem ID; immutable revision ID; native Problem FK/code;
package SHA-256; canonical deployment manifest digest; converter/worker pins;
checker language/flags; exact limits/language overrides; ordered case/display and
group mapping; statement/sample asset digests; publication/probe status. Allocate
an opaque code such as `pv` plus an 18-digit database revision ID (20 characters),
with database uniqueness and exhaustion checks; keep the full digest separately.
Never truncate a digest and assume collisions cannot happen.

1. Convert in a fresh private staging directory. Reject unsupported metadata;
   preserve checker CPP17/CPP23, points, dependencies and limits. Do not run upload
   scripts. Canonical manifest lists sorted relative paths, sizes and file hashes
   (including init.yml/data.zip/checker/header), converter pin and configuration.
2. Transfer privately using an authenticated operator/deployment channel; the
   judge protocol does **not** transfer test data. Worker-side trusted installer
   verifies all hashes, no symlinks/escapes and exactly one code/path. Install by
   atomic rename into an immutable read-only final path on the same filesystem.
3. Record an authenticated readiness receipt bound to worker identity, boot/session
   generation, image/compiler identities, code and manifest digest. Verify all
   required solution **and checker** executors and an isolated known-result probe;
   a native CPP23 language advertisement alone is insufficient. Never expose the
   receipt's private manifest/case filenames to participants.
4. Trigger supported-problem refresh and confirm exact code advertised. Gate
   publication on metadata/assets, eligible worker receipt and successful probe.
   Transactionally publish the contest assignment. Failed staging leaves old
   published versions available; imported versions can exist privately beforehand.

For the initial one-worker M1, install only the approved immutable version on
that worker and verify the receipt before operator dispatch. For the future pool,
add a small **bridge-local** readiness predicate to `JudgeHandler.can_judge` and
ensure both direct and queued `JudgeList` selection call it: native code/executor
checks AND current verified receipt AND required compiler/checker/runtime/image
AND approved contest CPU pool. Resolve requirements through the submission's
pinned context; changing the queued item/call signature locally is required if
the same code can occur in contests with different approved pools. The future contest-pool call-signature change is not implemented; C11 gates
the initial single worker through existing native calls. Persist eligibility in coordinator state and fail closed
after receipt invalidation, worker reconnect, revocation or changed deployment.
Both scheduling paths must enforce this even for explicit judge targets.

An explicit `judge-id` exists only on the site-to-bridge request and constrains a
single named worker; it is not a worker-pool or hash guarantee. Handler-level
`can_judge(..., judge_id=own_name)` bypasses its disabled check, while other queue
paths apply disabled/tier filters differently. Revalidate readiness regardless of
target/disabled state; do not use disable toggles as a digest gate. The native
global minimum tier can starve a compatible higher-tier worker; use one approved
tier initially and test queue behavior before introducing heterogeneous pools.

## Cache, update and lifetime rules

`judgeenv` caches root directories and code-to-root lookups. Refresh clears the
directory-list cache, **not** the code-to-root dictionary while the previous
init.yml still exists. Filesystem watcher/SIGUSR2/control POST `/update/problems`
request list refresh; their success does not validate bytes. The updater contains
a comment acknowledging its grading synchronization is broken. Never depend on
refresh to make an in-place test replacement safe.

Each grading worker creates a new `Problem`, parses init.yml, opens data.zip and
maintains per-Problem checker modules; `ProblemDataManager` reads local files or
the ZIP. Immutability avoids open-archive and cache races. Old directories remain
until no queued/running/rejudge/reference/retention requirement uses them.

Bridged C/C++ checkers compile through `compile_with_auxiliary_files(cached=True)`;
the LRU key combines executor class/module and a C-like key containing command,
architecture, defines, flags, link flags and source byte values. It does not
attest compiler binary/image bytes or the deployment manifest. Auxiliary paths
are converted to basenames, so reject basename collisions. Restart/re-enroll the
worker for compiler/image updates; give new data/checker versions new codes.
Worker grading subprocess cleanup clears its compiled executor objects; do not
assume a global distributed cache or cache invalidation protocol.

Sources: [judgeenv](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/judgeenv.py),
[Problem/data](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/problem.py),
[watcher](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/monitor.py),
[judge lifecycle](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/judge.py),
[auxiliary compilation](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/utils/helper_files.py),
[compiled cache](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/executors/compiled_executor.py),
[C-like key](https://github.com/DMOJ/judge-server/blob/1245dc4158dbb9e906c4c103e1ea939e012ee79b/dmoj/executors/c_like_executor.py).

## Submission pinning, corrections and rollback

At receipt, transactionally select active contest-problem revision and save native
Problem FK/code, immutable manifest, language and limit/rules snapshot. New native
Problem rows per revision make ordinary upstream dispatch resolve the right data;
block edits/deletion of referenced versions and their LanguageLimits. A display
alias/contest slot is separate from the native version. Standings aggregate the
same logical contest slot across revisions only under an audited correction rule.

The native protocol identifies results by `submission-id`; it has no distinct
attempt/generation token. Stock rejudge resets fields and deletes testcase rows.
Before correction, serialize each original submission's execution, abort/drain any
old worker, and create a distinct internal native execution Submission ID for the
new attempt/version, linked to the original immutable receipt/source. Keep only
the original contest receipt in official attempt counting; the execution record
must have no official ContestSubmission. Callback integration must apply its
result once to the original receipt only when the linked attempt is authoritative,
with stale events rejected and old results retained privately. This is a bounded
extension to native submission/results, not an implemented guarantee. B04/B09 and
F10/F11 must verify it; ordinary rejudges retain the same version unless an explicit
correction authorizes a new one. Rollback changes future assignments; rejudging old
receipts against a rolled-back version is a separate audited correction operation.

Required future checks: wrong digest never schedules; stale/reconnected receipt
fails closed; missing checker runtime blocks readiness; distinct old/new codes
judge their own data concurrently; duplicate roots rejected; both queue paths and
explicit target respect approved pool; late old callbacks cannot overwrite the
new attempt; reference/history/retention prevents premature version deletion.
No unresolved protocol-field assumption blocks this **design**. Implementation,
actual routing, checker handshake and result-attempt behavior remain Phase B/C/F/G
verification work; A03 CLI evidence does not prove them.
