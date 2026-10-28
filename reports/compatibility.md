# Compatibility report

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
