# Compatibility report

A03 isolated judge reproduction (2026-10-28): **PASS**, independently reviewed.
The existing runner exited **0** in fresh `build/a03-judge-1/pipeline/` using the
same pinned image, source commits, compiler standards, limits and sandbox settings.
[Latest A03 evidence/commands](a03-judge-1/README.md),
[independent review](a03-judge-1/review.json), [score assertions](a03-judge-1/scores.json),
[live sandbox inspection](a03-judge-1/sandbox.json).

| Actual real-package probe (CPP23) | Exact observed verdicts | Sum of asserted case points |
| --- | --- | --- |
| Reference | 103 AC | 103 |
| Well-formed all-NO | 55 WA / 48 AC | 48 |
| Runtime | 103 RTE | 0 |
| Timeout | 103 TLE | 0 |

All **18 probes / 454 ordered case records and score assertions** passed. This is
**452 executed cases plus 2 intentional dependency skips**, recorded SC/zero points
rather than AC; no missing/skipped executor, skipped probe or failed assertion
counts as PASS. Synthetic tokens/multiple probes cover AC/WA/RTE/TLE, alternative
valid outputs and presentation feedback; grouped probes verify 30/50/20,
30/0/0, 0/0/20, 0/0/0 and expected dependencies. Totals above are asserted judge
case points, not website standings.

Independent preflight found that ungrouped probes lacked score assertions. The
focused probe-installer change adds numbered `score_cases` using configured points
for AC and zero for failures; explicit group arrays stay unchanged. Six targeted
regression tests passed. The official pinned DMOJ TestManager asserts every
`result.points`; ordinary CLI case lines do not emit a separate numeric score trace.
The reviewer independently checked expectations, original bytes/standards/limits,
all logs and score assertions, runtime locks and raw live-container restrictions.

Executed image: `sha256:d8d9dded026cd9d2d4a4f41136b99fa935935f8638cab314ad0a0e567ebcf0e8`.
DMOJ commit: `1245dc4158dbb9e906c4c103e1ea939e012ee79b`.
Full base digest, compiler/package versions and commands/exits are in
[A03 evidence](a03-judge-1/evidence.json). No image rebuild or pin/sandbox changes.
Raw logs, imported files and solutions remain ignored; previous evidence is retained.

Coverage is still one real export plus synthetic fixtures with one case per group.
Multi-case group semantics, jury internal errors, exact Polygon toolchain/timing
parity, website/bridge/standings and multi-worker recovery/capacity remain untested.
A04 has not started. Earlier measured results and blocked attempts follow for
historical context; A02 remains a conversion-only result, separate from judging.

Judging milestone resumed 2026-10-28: **PASS for the supplied gaming-grid package
and all three synthetic packages**. This is actual execution by the pinned DMOJ
engine and its supported `dmoj-cli test` command, including bridged testlib checkers.
Docker client/server **29.9.2** passed `docker info` and `hello-world` after refreshing
the session group with `sg docker`; no daemon/socket permissions were changed.

| Actual DMOJ check | Observed result |
| --- | --- |
| Real reference, CPP23 | **103 AC** |
| Real well-formed all-NO probe, CPP23 | **55 WA / 48 AC**, matching every expected case; empty feedback assertion excludes presentation errors |
| Real runtime probe, CPP23 | **103 RTE** |
| Real timeout probe, CPP23 | **103 TLE** |
| Synthetic groups | All four probes pass, including point assertions 30/50/20, 30/0/0, 0/0/20, 0/0/0 and dependency skips |
| Synthetic multiple-answer checker | Accepted and alternative solutions AC; wrong and presentation outputs WA; RTE/TLE probes pass |
| Synthetic token checker | AC/WA/RTE/TLE probes pass |
| Conversion / independent preservation | Four conversions pass; real 103 test pairs, 15 statement assets, sample pair, checker/header bytes and limits verified |
| Unit tests | **11 passed** |

All **18 probes / 454 case records** completed with exact expected verdicts and
successful official tester assertions. No skipped executors, compilation failures,
judge exceptions, missing cases or mismatched source metadata were accepted.
The real checker and reference retain CPP23, **2 seconds / 262144 KiB**. Python in
the runtime is **3.14.7**; compiler **GCC 16.2.0**, C++23 `__cplusplus=202302L`.
This validates Linux execution, not replication of Polygon's MSYS2 GCC14 toolchain.
The 2-second limit is passed unchanged to DMOJ; its periodic enforcement terminates
the busy-loop probe at about 4 seconds on this worker. These tests verify the TLE
verdict, not precise timing parity with Polygon.

Runtime base: `dmoj/runtimes-tier1@sha256:dc5cba4a00fdaca99a7b597d2451fb8b4e731574949593cc52f4291d3e5189f1`.
Executed image: `sha256:d8d9dded026cd9d2d4a4f41136b99fa935935f8638cab314ad0a0e567ebcf0e8`.
Judge commit: `1245dc4158dbb9e906c4c103e1ea939e012ee79b`.
The base digest is the Dockerfile default; build/runtime Python packages are pinned
in `requirements-judge.txt`, and isolated metadata records the installed versions.

The first execution exposed a concrete CLI integration issue: `ProblemConfig`
wraps YAML lists in `ConfigNode`, so the tester's list check misses per-case verdict
and score lists. Numbered mappings fix both fields. A regression test and the actual
group/real judging run verify the correction. The entrypoint loads only supported
C++ executors, retaining their self-tests; unrelated Objective-C initialization had
raised a TypeError during the initial attempt. That failed attempt was stopped
before its remaining timeout probes and remains private under ignored `build/`.

Repeat the validated run (choose a new output directory each time):

```sh
sg docker -c 'docker info'
sg docker -c 'docker run --rm hello-world'
sg docker -c 'docker build -f Dockerfile.judge -t cp-judge-compat .'
sg docker -c 'PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -m tools.pipeline --output build/judging-milestone-docker-resume-3 --real local-packages/gaming-grid.zip --judge'
.venv/bin/python -m tools.verify_install local-packages/gaming-grid.zip build/judging-milestone-docker-resume-3/converted-3
PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -m unittest discover -s tests -v
```

The pipeline exited **0**. [Sanitized evidence](judging-docker-resume.json) includes
image/source pins, versions and every probe's observed counts. Raw logs and package
contents remain in ignored `build/` and `local-packages/`; nothing was committed or
pushed. The existing network isolation, read-only mounts/root, unprivileged user,
capability restrictions and resource caps are preserved.

Coverage is limited to this real package and the synthetic fixtures. Multi-test
all-or-nothing groups, jury internal-error behavior, website import/rendering and
standings remain **NOT TESTED**. Generators/validators are not executed; previously
rejected formats and partial checker point protocols remain unsupported. Website
implementation has not started. Earlier attempts and the source audit below are
historical evidence, superseded by the current measured results above.

Historical attempt after Docker installation (2026-10-28):
**BLOCKED by Docker socket permissions before image build**.

Docker is now installed: client **29.9.2**, buildx **v0.38.1**, Compose **v5.6.1**.
The server version cannot be queried. Both commands below exit **1**, including
when retried outside the workspace sandbox:

```text
docker info
docker run --rm hello-world
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

`docker pull dmoj/runtimes-tier1:latest` also exits **1** with that exact error.
`sudo -n docker info`, outside the workspace sandbox, exits **1** with
`sudo: interactive authentication is required`. No daemon, socket or group
permissions were changed. The runtime digest could not be resolved; no image was
built, and the base digest, image ID, executed judge version and compiler/runtime
versions remain **null / NOT TESTED**. No build/runtime failure can yet be diagnosed
beyond the Docker access failure.

Fresh pipeline command:

```sh
PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -m tools.pipeline --output build/judging-milestone-docker-resume-1 --real local-packages/gaming-grid.zip --judge
```

It exits **2** after all four conversions pass, at
`docker image inspect cp-judge-compat`, which returns the same socket permission
error. Its report and error log are retained privately under that ignored output
directory. Independent `tools.verify_install` verification passes for all **103**
input/output pairs, **15** statement assets, the sample pair, checker/header bytes,
limits and configuration. The generated real-problem probe configuration confirms
the expected **55 WA / 48 AC** split and preserves CPP23. All **10** existing unit
tests pass with Python **3.14.4** and the clean pinned converter
`41ce3afcedf6c02793b308ba2e6ddb2ea5f82134`; these are conversion and result-validation
checks, not DMOJ execution. [Historical socket-permission evidence](judging-milestone/docker-permission-evidence.json)
records the commands, versions, expectations and null runtime observations.

The existing converter, Dockerfile, CPP23 declarations, sandbox restrictions and
strict result validation are unchanged. No AGENTS.md was present in the workspace
or its parent directories. Fixture expectations still require reference **103 AC**,
all-NO known-wrong **55 WA / 48 AC**, runtime **103 RTE**, and timeout **103 TLE**.
These counts are expectations, not actual DMOJ results; synthetic checker,
alternative-answer, presentation, scoring and dependency probes likewise remain
**NOT TESTED** in DMOJ. Skips, compilation failures and judge errors cannot pass.

Smallest next action: an administrator must make `docker info` and
`docker run --rm hello-world` succeed **in this session** (or supply an accessible
Linux Docker worker). Then resolve and pin the runtime digest, build the existing
image, and run the pipeline in another fresh output directory. **Website work has
not started; the judging milestone remains incomplete.** Private packages and raw
logs remain under ignored `local-packages/` and `build/`.

The previous attempt, before Docker installation, follows for traceability.

Previous judging milestone attempt (2026-10-28): **BLOCKED before image build**.
The converter/adapter and supported input formats are unchanged. A fresh pipeline
run converted all four existing packages, but no DMOJ submissions have executed.

- `docker build -f Dockerfile.judge -t cp-judge-compat .` returned **127**:
  `docker: command not found`. See [build log](judging-milestone/docker-build.log).
- The attempted administrator prerequisite check, `sudo -n true`, returned **1**:
  `sudo: interactive authentication is required` (outside the workspace sandbox).
  No system packages or daemon configuration were changed.
- Smallest next action: an administrator must install/start Docker on this Linux
  worker and make `docker info` work for the session, or provide an accessible
  Linux Docker worker. The agent cannot supply interactive sudo authentication.
- [Sanitized evidence](judging-milestone/evidence.json) records tested converter
  and requested judge pins; executed judge commit, base-image digest, built image
  ID and compiler/runtime versions are explicitly **null / NOT TESTED**.
- [Fresh pipeline report](judging-milestone/pipeline.json) and
  [log](judging-milestone/pipeline.log): conversion PASS, judging NOT TESTED,
  pipeline exit 2. Command:
  `PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -m tools.pipeline --output build/judging-milestone-1 --real local-packages/gaming-grid.zip --judge`.
- [Ten tests pass](judging-milestone/unit-tests.log), using
  `PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -m unittest discover -s tests -v`.
  These verify conversion and result validation using synthetic log examples;
  they are **not** actual DMOJ judging evidence. Python compilation, shell syntax
  and Git whitespace checks also pass.

Review against the clean pinned DMOJ source confirms the existing command shape:
`dmoj-cli -c /config.yml --history /tmp/history --no-ansi test <problem IDs>`.
`commands/test.py` reads `init.yml:tests`; `testsuite.py` supports `language`, `time`
(seconds), `memory` (KiB), `cases`, `score_cases` and feedback expectations. Its
missing-language branch returns zero after printing `Skipped`; the runner rejects
that outcome. `DMOJ_IN_DOCKER=1` loads `/judge-runtime-paths.yml`. Unprivileged
execution and `SYS_PTRACE` match the upstream Docker setup; read-only mounts,
network isolation and resource caps remain enabled. Build/sandbox execution has
**not** been confirmed; no claim is made that static review establishes runtime
compatibility. The official entrypoint's writable `pip install -e` step is avoided
because this container deliberately has a read-only root; the image installs DMOJ
at build time and invokes its supported CLI directly.

The real checker and reference retain **CPP23**, never a C++20 fallback. Its old
`-999` probe was only malformed-output rejection. The replacement reads the input
case count and prints well-formed `NO` answers. The private jury answers imply
**55 WA and 48 AC** across the 103 tests; these are **expected**, not observed.
The checker source's genuine mismatch path calls `_wa` when participant NO meets
jury YES. A blank feedback assertion excludes DMOJ's `Presentation Error` fallback
for testlib exit 2. Reference expects 103 AC; RTE and TLE probes each cover 103 tests.
Existing synthetic token, alternative-answer, presentation and group probes remain.
No checker source, hidden input, jury answer or reference source is added to Git.

The runner now verifies sequential case numbers and exact expected verdicts in
addition to the official tester's assertions. It separates missing/skipped
executors, checker/judge internal errors, compilation failures and incomplete logs
from contestant verdicts. A truncated 102-case reference log cannot report PASS.
It records the actual image ID, runtime-base label and isolated runtime/package
versions before grading; execution uses the image ID rather than a mutable tag.
PASS also requires a digest-pinned runtime base and matching judge source metadata.
The Docker recipe remains the existing upstream-based recipe with metadata capture,
not a replacement pipeline. None of these container paths could be exercised yet.

After Docker is available, build with the resolved immutable base (see README),
then rerun the pipeline with a new output directory, preserve its private raw logs
under ignored `build/`, and commit only sanitized summaries. Investigate concrete
build, CPP23 self-test, sandbox or jury failures without accepting skips as success.
**Website import and standings remain NOT TESTED.**

The original conversion/audit evidence follows unchanged for traceability.

Measured 2026-10-28 on Ubuntu 26.04.1, x86-64, Python 3.14.4.
**Conversion is verified for the supplied real package; end-to-end Polygon → DMOJ
judging compatibility is NOT TESTED.** Docker and the DMOJ runtime are absent.
No checker, generator, reference solution or submission was executed on this host.

| Check | Result | Evidence / limitation |
| --- | --- | --- |
| Pinned converter license/source audit | PASS | MIT; audit below and upstream-audit.log |
| Original Polygon → Hydro scoring fidelity | FAIL | Reader has no scoring/group/dependency fields; writer emits one 100-point subtask |
| Unadapted DMOJ writer memory units | FAIL | Emits memory_limit: 64 for a 64 MiB fixture; submission API requires 65536 KiB |
| Strict adapter + writer, three synthetic cases | PASS | unit-tests.log, synthetic-preservation.json |
| Real gaming-grid package conversion | PASS | 103 tests; source hash in real-preservation.json |
| Real inputs and expected outputs | PASS | All 103 pairs byte-identical; includes sample among active tests |
| Real statements and samples | PASS | 15 statement/section assets and sample pair byte-identical; rendering/site import NOT TESTED |
| Real checker + header preservation | PASS | Byte-identical; source standard preserved as CPP23 |
| Limits and rounding | PASS | Real 2000 ms → 2 s, 268435456 bytes → 262144 KiB; synthetic odd-byte limit rounds up |
| Group points and dependencies | PASS | Synthetic 30/50/20 groups, second depends on first; configuration only |
| Accepted/wrong/multiple-answer judging | NOT TESTED | Expected probes installed; no Docker executable |
| Runtime error and time-limit verdicts | NOT TESTED | Expected RTE/TLE probes installed; no judge execution |
| Checker verdict mapping / jury errors | NOT TESTED | Source mapping inspected; no behavioral execution |
| Group dependency skipping / partial scores | NOT TESTED | Expected AC/WA/SC and case scores installed; no judging |
| Multi-test all-or-nothing group scoring | NOT TESTED | Initial synthetic fixture has one test per group |
| DMOJ website score aggregation | NOT TESTED | No site/application in scope |
| Container build, sandbox and runtime versions | NOT TESTED | Docker unavailable; recipe remains unvalidated |

The real package is an existing Polygon export, revision 6, short name `gaming-grid`,
with a standard batch testset, pre-generated inputs/answers, checker, reference C++
solution, HTML/TeX/PDF statements and no groups. Its source type names an MSYS2
GCC14 C++23 toolchain: it is **not verified to be a full Linux export**. No binaries,
generators or scripts were used. Please supply an actual Polygon **full Linux**
export, especially a grouped problem and a standard token-checker problem, for
real-package coverage of those cases. Synthetic tests do not establish that coverage.
Private export contents are excluded from Git; the report contains only counts/hashes.

Audited source pins:

- [Problem-Change-Center 41ce3af](https://github.com/Albert-Li-Sz/Problem-Change-Center/tree/41ce3afcedf6c02793b308ba2e6ddb2ea5f82134), MIT (Albert_Li, 2026).
  `runner/package_converter.py:_run_polygon_route` invokes `p2h_safe.py` to Hydro,
  then `read_hydro` and `write_dmoj`. It is not a native Polygon→DMOJ reader.
  `runner/Dockerfile` installs defusedxml, PyYAML, polygon2hydro at `93aca21` and
  Polygon2DOMjudge at `8b0919a2a3e0946faaf677ec5cb2cad65fee7e30`; backend/web
  requirements include FastAPI/Uvicorn, multipart, pytest, httpx2 and are not needed
  by our writer-only integration. The upstream wrapper defaults to `--no-run-doall`.
- [polygon2hydro 93aca21](https://github.com/KisuraOP/polygon2hydro/tree/93aca21db49131baa0ca3077d6fec037ac52b5e6), MIT.
  `polygon_reader.py:read_problem` converts statements to Markdown, scans tests,
  extracts checker filename, and floors bytes to MiB. Its dataclass lacks groups,
  scores and dependencies. `hydro_writer.py:_build_config_yaml` creates a single
  100-point min subtask. The read-only audit directly invokes these implementations
  on our synthetic grouped fixture; it does not exercise the whole PCC wrapper.
- PCC `package_adapters.py:write_dmoj` preserves IR groups/dependencies when supplied,
  but removes sample-marked cases from active judging, emits memory in MiB,
  and picks CPP20 for any C++ checker. The adapter keeps every test active, explicitly
  copies sample sidecars, fixes memory units in ZIP and installed directory, and
  preserves declared C++11/14/17/20/23 standard. Every statement/support asset is
  also kept verbatim rather than depending on the selected display sidecar.
- [DMOJ 1245dc4](https://github.com/DMOJ/judge-server/tree/1245dc4158dbb9e906c4c103e1ea939e012ee79b), AGPL-3.0-or-later.
  Inspected `README.md` Docker setup (`SYS_PTRACE`), `.docker/tier1/Dockerfile`,
  `dmoj/commands/test.py`, `testsuite.py`, `problem.py`, `judge.py`,
  `checkers/bridged.py` and `contrib/testlib.py`. Testlib exit 0 maps AC, 1 maps WA,
  2 maps WA with presentation feedback, 3 raises InternalError. Exit 7 uses DMOJ's
  integer `points N` protocol; we reject known partial-point checker patterns instead
  of assuming Polygon's protocol matches. Arbitrary native checker semantics still
  need execution tests; static pattern detection cannot prove compatibility.

Explicit limitations: one root `problem.xml`, one testset, standard batch with
stdin/stdout, complete-group scoring with positive integer points and dependencies
only on earlier groups. Reject file I/O, multiple runs/testsets, interactors,
unknown judging/testset/per-test policies, missing checker/answers, unsupported
C++ standard, nested checker includes, zero/fractional group points and known partial
checker scoring protocols. Checkers must be source-based testlib C++; built-in IDs
without source do not trigger a fallback. Inputs must already exist; generator,
validator and package script behavior is reported as not executed. Exact compiler
version/platform, nonstandard checker protocols, resources referenced outside the
statement directories and arbitrary additional Polygon extensions are not validated.
Statement assets are inert judge attachments; there is no web/database installation.

Executed commands (PCC_ROOT points to the clean pinned checkout under /tmp):

```sh
PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -m unittest discover -s tests -v
# exit 0: 6 tests, including all three fixtures and adversarial inputs
PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -m tools.audit_upstream /tmp/cp-judge-p2h
# exit 0: confirms reader scoring loss and unadapted writer units
PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -m tools.pipeline --output build/final-run --real local-packages/gaming-grid.zip --judge
# exit 2: all four conversions PASS; judging NOT TESTED, docker executable missing
.venv/bin/python -m tools.verify_install local-packages/gaming-grid.zip build/final-run/converted-3
# exit 0: independent byte/limit/config verification
```

See README.md for repeatable setup and isolated judge commands. The next blocking
step is to build/run that image on a dedicated Docker worker, retain judge.log,
resolve runtime/compiler/sandbox failures, and record the immutable image digest
and installed versions. No end-to-end compatibility claim is warranted yet.
