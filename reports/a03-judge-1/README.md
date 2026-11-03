# A03 isolated judging reproduction — PASS

Measured 2026-10-28 with the existing pinned DMOJ Docker runner, a fresh output
directory, and one independent reviewer. Pipeline exit **0**; all **18 probes**
completed with **454 exact case-verdict and per-case score assertions** verified.
Those records include **452 executed cases and 2 expected group dependency skips**
(SC, zero points); no unavailable executor, skipped probe, missing case or failed assertion
was accepted as success.

| Problem/probes | Verified verdicts and sum of asserted per-case points |
| --- | --- |
| Real gaming-grid reference, CPP23 | 103 AC; 103 points |
| Real well-formed all-NO, CPP23 | 55 WA / 48 AC; 48 points; empty feedback assertion excludes presentation errors |
| Real runtime / timeout, CPP23 | 103 RTE / 103 TLE; zero points each |
| Synthetic groups | accepted AC/AC/AC → 30/50/20; easy-only AC/WA/WA → 30/0/0; dependency WA/SC/AC → 0/0/20; wrong WA/SC/WA → 0/0/0 |
| Synthetic multiple | accepted and alternative: 3 AC / 3 points each; wrong and presentation: 3 WA / zero points; runtime: 3 RTE / zero; timeout: 3 TLE / zero |
| Synthetic tokens | accepted: 3 AC / 3 points; wrong: 3 WA / zero; runtime: 3 RTE / zero; timeout: 3 TLE / zero |

The reviewer identified a preflight coverage gap: only grouped probes previously
specified score assertions. A focused change in `tools/install_judge_tests.py`
adds numbered `score_cases` to all remaining probes: configured case points for
AC, zero for expected failure verdicts. Existing explicit group scores are retained.
Six targeted tests passed, including mixed real verdicts and non-unit case points.
No checker, solution, limit, compiler standard, dependency pin or sandbox setting
was changed. The converter, runner and Docker image were not replaced or rebuilt.

Score verification uses the pinned official DMOJ `TestManager` assertions on each
`result.points`, alongside complete per-probe Success and exact case sequence.
The CLI's ordinary case lines do not print numeric scores; the totals above are
sums of successfully asserted per-case values, not a separately logged score trace
or website standings calculation.

Executed immutable image:
`sha256:d8d9dded026cd9d2d4a4f41136b99fa935935f8638cab314ad0a0e567ebcf0e8`.
Base:
`dmoj/runtimes-tier1@sha256:dc5cba4a00fdaca99a7b597d2451fb8b4e731574949593cc52f4291d3e5189f1`.
DMOJ: `1245dc4158dbb9e906c4c103e1ea939e012ee79b`.
Docker server 29.9.2; Python 3.14.7; GCC 16.2.0. Synthetic checkers retain CPP17,
synthetic solutions CPP20, real checker/reference/probes CPP23. All required
executor self-tests and locked runtime package comparisons passed.

Live `docker inspect` confirmed user `judge`, no network, read-only root and two
read-only problem/config mounts, all capabilities dropped except SYS_PTRACE,
no-new-privileges, 128 PIDs, 2 GiB, 2 CPUs and executable ephemeral `/tmp`.
The stale host group session required `sg docker`; no socket/daemon permissions
were changed. Existing historical evidence and A02 outputs remain intact.

[Evidence and runtime identity](evidence.json), [exact commands/exits](commands.json),
[independent review](review.json), [expected verdict/score coverage](expectations.json),
[verified score assertions](scores.json), [live sandbox](sandbox.json),
[official runner report](pipeline.json), [targeted test output](probe-tests.log).

Recorded runner command (choose a new output directory to reproduce):

```sh
sg docker -c 'PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -B -m tools.pipeline --output build/a03-judge-1/pipeline --real local-packages/gaming-grid.zip --judge --judge-image sha256:d8d9dded026cd9d2d4a4f41136b99fa935935f8638cab314ad0a0e567ebcf0e8'
```

The actual recording wrapper and timestamps are listed in commands.json.
Raw judge logs, configs, solutions and private imported data remain only under
ignored `build/a03-judge-1/`; do not publish those files. The sanitized evidence
records the raw log's hash for audit matching.

Limits: one real export and three synthetic packages, one test per synthetic group,
no precise Polygon toolchain/timing parity or jury-internal-error coverage. TLE
verdicts do not establish precise limit-boundary enforcement. Website import,
rendering, bridge dispatch, standings, multiple-worker recovery and load remain
untested. **A04 was not started. No commit or push was performed.**
