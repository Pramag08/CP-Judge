All three packages produced by `python -m tools.make_fixtures` are **SYNTHETIC**.
Our fixture XML, statements, checker sources and probes are covered by the repository MIT license.
`testlib/testlib.h` is upstream Mike Mirzayanov testlib at
`3bf5ba5aca6007bf8dcde6d00949ec3116ee3cc7`, distributed under its adjacent MIT LICENSE.
No private Polygon test data or reference solution is redistributed.

| Case | Input / checker | Expected probes |
| --- | --- | --- |
| tokens | sum; whitespace-insensitive, case-sensitive tokens | AC, WA, RTE, TLE |
| multiple | any even integer in [1,n]; jury answers 2 | 2 AC, 4 AC, -999 WA, extra tokens WA, RTE, TLE |
| groups | sum; 30-point easy, 50-point hard depends on easy, 20-point independent | all AC; easy only 30; failed easy skips hard, independent earns 20; all wrong 0 |

Points in the last row are intended batch totals. DMOJ's official test harness
asserts individual verdicts/points and dependency skips. Site-level score aggregation
is outside this repository and is NOT TESTED. The initial grouped fixture has one
test per group; multi-test all-or-nothing batches remain NOT TESTED.

Every package has one sample, still included among the active judging tests, and
separate sample sidecars. ZIP generation uses fixed ordering and timestamps.

The gaming-grid real-package probe now prints valid `NO` tokens rather than `-999`.
Its expected 55 WA / 48 AC checks semantic mismatch; testlib presentation errors
are excluded by feedback expectations. The reference, all probes and the checker
retain the real package's declared CPP23. On 2026-10-28 these probes passed in the pinned DMOJ engine: reference 103 AC,
known-wrong 55 WA / 48 AC, runtime 103 RTE, timeout 103 TLE. All synthetic probes
also passed, including group point assertions and dependency skips. See
[the compatibility report](../reports/compatibility.md).
