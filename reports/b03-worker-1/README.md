# B03 — authenticated local worker

**PASS for B03; independent review PASS.** [Lifecycle acceptance](acceptance.json),
[independent review](review.json), [commands/exits/logs](commands.json).
No problem was imported and no website submission was judged. B04 is NOT STARTED.

## Pinned worker and native registration

Reused A03's exact image
`sha256:d8d9dded026cd9d2d4a4f41136b99fa935935f8638cab314ad0a0e567ebcf0e8`,
DMOJ `1245dc4158dbb9e906c4c103e1ea939e012ee79b`, original autoconfig compiler
paths and GCC **16.2.0**. No rebuild/package installation/pin change. The former
`/tmp/cp-judge-dmoj` checkout is absent; inspected the actual image's pinned source.
The selected website source remains `604d60cfd764bc708b04ffd75b715a5398b91f8b`.
Upstream attribution/licenses and prior reports are preserved.

Created only the native Judge authentication record `cpjudge-local-worker` with
a generated private key. Host credentials/config are ignored under
`build/b03-worker-1/private/` (directory0700/files0600); the site receives the
matching registration through stdin into a mode0600 file. No key in argv,
environment, reports or Git. Existing accurate `CPP23`/`GNU C++23` metadata was
reused unchanged; zero Language rows added/edited. RuntimeVersion rows and online
state are produced solely by upstream authentication/handshake/disconnect code.

Native startup self-tests succeeded for **CPP11, CPP14, CPP17, CPP20 and CPP23**.
The handshake advertises `g++11/14/17/20/23` version **16** (upstream major-version
parser); full `-dumpfullversion` is independently **16.2.0**. Kept both accurately.
Harmless executor compilation/execution measured `__cplusplus` values
201103/201402/201703/202002/202302; CPP23 also compiled/executed `std::expected`.
See the final `capabilities-*.json` and native worker self-test/handshake logs.
These diagnostics use native executor APIs, not website submissions or packages.

## Connection and sandbox

Worker shares only the existing site's **network namespace**, connecting to the
unpublished loopback bridge at127.0.0.1:9999. No host networking or new published
ports. Judge PID/filesystem namespaces remain separate. The trusted supervisor
can reach coordinator services; submitted programs retain native syscall and
filesystem restrictions. Six AF_INET/AF_INET6/AF_UNIX stream/datagram socket
attempts per executor returned EACCES, and reading `/config.yml` was denied.
This focused isolation check is not an exhaustive sandbox audit.

The pinned image's `DMOJ_IN_DOCKER=1` would implicitly start an unauthenticated
API on9998, conflicting with the site bridge. Set it empty and explicitly merge
the exact `/judge-runtime-paths.yml` into the private config. Source inspection
confirms this flag is used only for the API/config/problem-path defaults. No
worker API is enabled, and no compiler/sandbox policy was changed.

Live inspection confirms user `judge`, read-only root and only two read-only
mounts (private config and **empty** problems directory), all capabilities dropped
except SYS_PTRACE, no-new-privileges,128 PIDs,2GiB,2 CPUs, executable ephemeral
1GiB `/tmp`. No Docker socket, home, website source/settings, or unrelated secrets
are mounted. Transport uses native key authentication over container loopback;
TLS is not enabled or claimed. See `sandbox-*.json`.

## Lifecycle and actual checks

```sh
python3 -B deploy/site-local/manage.py start
python3 -B deploy/site-local/manage.py stop
python3 -B deploy/site-local/manage.py status
# Worker only, with website/support already running:
python3 -B deploy/site-local/b03.py start
python3 -B deploy/site-local/b03.py stop
python3 -B deploy/site-local/b03.py status
```

The existing manager starts DB/Redis/web/bridge/events/Celery before the worker,
and stops the worker before bridge and DB. A host flock serializes worker actions;
the uniquely named, B03-labelled, exact-image container is reused. Repeated full
start retained the same container ID and PID. Full stop observed all five
containers stopped, then full start reconnected the actual worker.

The B02 bridge guard now permits only this privately matched owned registration;
it still refuses unknown judges or **any in-progress jobs**. Direct bridge stop
also refuses online judges. Upstream bridge reset logic is unchanged. This idle
local lifecycle does not establish official-job recovery and is intentionally
conservative until later operations tasks.

Actual disconnect set native online=false, deleted RuntimeVersion rows and hid
the worker on native `/status/` (HTTP200); reconnect authenticated again, restored
all five runtimes and reappeared. `state-*.json` preserves online/offline samples.
Initial default-SIGTERM stops reached Docker's timeout because native PID1 did
not handle it. Final stop explicitly uses **SIGINT**, the native KeyboardInterrupt
cleanup path; focused stop/status/start/verify passed with exit_code0,
OOMKilled=false and real offline→online transitions. Earlier results remain.

Currently running: website at http://127.0.0.1:8000/, MariaDB, Redis, native
bridge, Celery, event daemon and authenticated judge worker. The worker advertises
zero problems. Use `setup` only for first enrollment against an established B01/B02
deployment; ordinary start/status/verification never rotates keys or resets accounts.

## Evidence and preservation

Exact subprocess argv/exits/timestamps/log paths are in `commands.json`. Principal
executed commands (repository root):

- `env CPJ_SITE_REPORT_DIR=/home/pramag/Documents/CP-Judge/reports/b03-worker-1 python3 -B deploy/site-local/manage.py start`: exit0.
- `python3 -B deploy/site-local/b03.py inspect`, `snapshot`, successful `setup`, `start`, `capabilities`, `acceptance`, `logs`, final `stop`, `status`, `start`, `verify`: each exit0. Snapshot/credentials are private; sanitized summaries are public.
- `env CPJ_SITE_REPORT_DIR=/home/pramag/Documents/CP-Judge/reports/b03-worker-1 python3 -B deploy/site-local/manage.py verify`: exit0, read-only checks and exact passwords; see ledger and verification report. The audit now reads actual Judge/RuntimeVersion counts (1/5) instead of its old literal zeros.
- `env CPJ_SITE_REPORT_DIR=/home/pramag/Documents/CP-Judge/reports/b03-worker-1 python3 -B deploy/site-local/manage.py status`: exit0; final native bridge/Celery counts1 each, event daemon running, worker online, website/DB/Redis Up.
- `python3 -B reports/b03-worker-1/verify_evidence.py`: exit0; saved results, reviewed hashes, prior-file preservation and credential exclusion passed; `git diff --check`: exit0. [Final audit](evidence-audit.json).

Failed explorations retained: initial `setup` exit1 conservatively rejected the
already-correct name `GNU C++23` (transaction rolled back); a premature `start`
exit1 found no container; initial `verify` exit1 wrongly expected full versions
instead of upstream-advertised major16. Corrected assertions preserve actual
metadata and versions; none of those failures is counted as passing acceptance.

Private exact snapshots compare all54 pre-existing model sets, every account/
password/session/problem/submission row and existing languages. Preservation
passed with202 migrations, zero new languages, exact deployed B01 overlay,
MathJax files and0153. No fixtures, resets or migrations were applied. Original
reports and dependency pins are unchanged. Independent reviewer inspected source,
configuration and execution evidence; did not rerun services or judging.

No B03 blocker. Retained limits: development/production warnings, unverified
browser cross-origin HTTP polling fallback, volatile event/Redis replay, idle-only
restart safety, no in-flight recovery/load/remote-TLS proof. Actual problem
installation, website judging, verdicts, checker compatibility and standings
remain untested. Next task: **B04 only when requested**. No commit/push.
