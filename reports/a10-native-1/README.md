# A10 — source mapping and narrow native checks

**COMPLETE for design and native branch investigation. Integration NOT TESTED.**

[Contract](../../docs/contracts/contest-native-mapping.md) records fixed settings,
native differences and bounded changes; [evidence.json](evidence.json) records
source hashes and actual observations. Source is clean A09 site commit
`604d60cfd764bc708b04ffd75b715a5398b91f8b`; files were compared to Git objects.

Executed command: `python3 -B reports/a10-native-1/probe.py` — **exit 0**.
The stdlib-only [probe](probe.py) runs native clock/scoring method bodies using
explicit cursor/query fixtures and the unmodified native ranker. It verifies
common-clock late entry, penalty examples, exact-deadline behavior, broad failure
filtering, duplicate timestamp behavior, fractional accumulation, full-case guards
and tied-rank differences. It does not execute SQL, Django ORM or any untrusted
submission, and does not validate an implemented CPJudge scoring extension.

No A02/A03/A09 expensive check was repeated; no service started or pin changed.
Native `time_limit=None` provides the desired common clock. Stock ICPC settings
alone do not implement full-AC-only credit, the exact failure set, stable first-AC
ordering, per-problem second flooring or shared competitive ties. B11 must add the
bounded preset and test MariaDB/real-result integration. B10/D08 must enforce the
strict server deadline and registration races. F10/F11 must fence rejudge results.

Blockers to A10 design: none. Runtime implementation and site/bridge/worker
compatibility remain untested and are Phase B/follow-up work, not A10 passes.
