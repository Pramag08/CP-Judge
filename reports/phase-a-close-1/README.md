# Phase A completion — A06/A07/A08/A10/A11/A12

**COMPLETE for specifications, source investigation and narrow native checks.**
A01–A05/A09 were verified from saved evidence and preserved byte for byte, not
rerun. No Phase B implementation, service startup, dependency installation,
conversion, actual judging, commit or push occurred. Website-to-worker and custom
Run compatibility remain **NOT TESTED**. Foobar **logo only, no adjacent text** is
now the branding specification; no frontend/preview was modified.

| Task | Contract/evidence | Result and remaining implementation |
| --- | --- | --- |
| A06 | [Permissions/identity/sessions](../../docs/contracts/permissions.md), [audit](checks-A06.json) | Resource/scope matrix, owner/delegate rights, private email/source/tests, unranked conflicts, college-ID uniqueness, temporary passwords and single-active-session replacement specified; enforcement untested |
| A07 | [Contest rules](../../docs/contracts/contest-rules.md), [audit](checks-A07.json) | Registration windows/races, common [S,E) receipt, removal retaining score versus DQ, full-AC/failure/tie/rejudge examples specified; lifecycle/scorer unimplemented |
| A08 | [AGENTS](../../AGENTS.md), [resume status](../../PROJECT_STATUS.md), [audit](checks-A08.json) | Working recipes, meaningful-check rules, source/runtime separation, exclusive ownership and per-task resume workflow documented |
| A10 | [Native mapping](../../docs/contracts/contest-native-mapping.md), [executed probe/report](../a10-native-1/README.md), [audit](checks-A10.json) | Native common clock and 75:00 penalty confirmed in isolated methods; exact-deadline, failure set, rounding/full-AC and tie gaps identified; bounded preset/guard specified |
| A11 | [Version/dispatch](../../docs/contracts/problem-version-dispatch.md), [executed probes/report](../a11-dispatch-1/README.md), [audit](checks-A11.json) | Immutable native codes, out-of-band digest/readiness receipts, caches and both routing paths specified; 4 native path/advertisement observations + 6 selection cases; no live routing |
| A12 | [Custom Run](../../docs/contracts/custom-input-run.md), [inspection/report](../a12-run-1/README.md), [audit](checks-A12.json) | Native custom packet unsupported/control /run 404 under isolated calls; dedicated executor adapter with compile/run isolation, numeric limits, quotas, privacy and results specified; no untrusted-code execution |

## Verification and preservation

Commands and failures: [commands.json](commands.json). Coordinator audits run
`python3 -B reports/phase-a-close-1/verify.py --task <ID>` after each task; all six
final task invocations exited **0**. Each checks local links, the 112-row acyclic
backlog and 90-task MVP dependency closure (Google C15 deferred), original
completed rows, exact selected-site Git source bytes, whitespace and preservation
of the 221 baseline files. Only four pre-existing files changed: AGENTS,
PROJECT_STATUS, implementation plan and MVP_DEPENDENCIES. Existing application,
converter, judge, fixtures, locks and prior reports are preserved.

`python3 -B reports/phase-a-close-1/verify.py --task final` is the combined final
audit, exited **0**. Its result is [checks-final.json](checks-final.json); later repeats preserve it under numbered
suffixes. Private baseline/status snapshots and six per-task shared-document
snapshots: `build/phase-a-close-1/`. The three subagent scripts verified immutable
source objects and used native function bodies with explicit fake attributes,
SQL-aggregate/query fixtures or temporary synthetic paths. No SQL/ORM, database,
HTTP server, real packet transport, compiler or sandbox executed in those probes.

Exploratory inventory `rg` returned 2 for nonexistent proposed directories and
restricted unrelated `/tmp` paths; scoped source paths were then resolved. The web
fetch of immutable GitHub pages returned cache misses, so source claims rely on
locally pinned files verified against their Git objects, not a successful web fetch.
An initial coordinator audit incorrectly treated the word DEFERRED inside a
selected task's description as deferring the whole task; it failed. The check was
corrected to test the task's status prefix. A task-status helper then failed on a
renamed marker, and the subsequent link audit failed on its not-yet-created report.
Both were corrected; failed invocations are retained in commands.json, not counted
as passes. No application defect was fixed or runtime result inferred from these.

## Decisions, blockers and next boundary

College-issued IDs/passwords replace the earlier Google/verified-email MVP
assumption; emails remain private contact data. New login replaces the old active
session per account, not a hardware/device lock. Current rule and contract text
controls over older historical source maps/reports. Removal retains earned score;
DQ excludes ranking. Receipt is sampled under transactional admission, with common
start/end and receipt/ID ordering. Rejudge uses a fenced authoritative replacement
and provisional withholding, not an additional official failed attempt. Version
readiness is separate authenticated deployment state; no invented DMOJ fields.

No unresolved **Phase A specification** blocker. Existing A09 migration-state
check is still failed (11 metadata differences, no DDL); MariaDB/deployment warnings
remain recorded in [A09](../a09-site-1/README.md). Native scorer/deadline changes,
readiness/attempt fencing and Run adapter are required future implementation.
Actual approved Foobar logo bytes are an outstanding UI input, not a Phase A gate.

**Next: B01**, bring up the pinned site/database using the A09 recipe as a baseline
for the integration proof. Reuse A09 startup evidence; do not repeat all its tests
without a reason. B02 then adds needed bridge services. No Phase B task started.
