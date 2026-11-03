# A02 converter reproduction — PASS

Measured 2026-10-28 using existing Python 3.14.4, PyYAML 6.0.3, defusedxml 0.7.1
and clean pinned PCC `41ce3afcedf6c02793b308ba2e6ddb2ea5f82134`.
No dependencies were installed; application code, fixtures and pins were unchanged.

- Six existing converter regression tests passed, including deterministic fixtures,
  odd-byte memory rounding, unsupported-feature/archive rejection and overwrite refusal.
- All four fresh conversions and existing `tools.verify_install` invocations passed:
  **112 input/output pairs, 4 sample pairs and 18 statement assets**, checker/header bytes,
  active samples, limits and supported group/dependency configuration.
- The supplemental read-only metadata audit checked CPP17 synthetic checkers,
  CPP23 real checker/reference probes, case ordering/membership, submission-limit
  propagation and every exported ZIP file against its extracted bytes. Synthetic
  fixture hashes match previous preservation evidence. Group points 30/50/20 and
  hard→easy dependency are preserved; ungrouped cases carry one point each.
- **Judging NOT TESTED.** No Docker, compiler, checker, solution or generator execution.
  Standards/limits/scoring were checked as metadata, not runtime behavior. Each
  synthetic group has one test; multi-test scoring, site aggregation, website and
  bridge integration, exact Polygon toolchain/timing and arbitrary exports remain untested.
  A03 has not started. Previous judge reports remain historical evidence.

[Exact commands and exits](commands.json), [test output](converter-tests.log),
[preservation](preservation.json), [metadata](metadata.json),
[conversion-only pipeline report](pipeline.json), [complete summary](evidence.json).
Every recorded verification command exited **0**. The executed supplemental audit
source is preserved as [metadata-audit.py](metadata-audit.py); its original command
used the byte-identical `build/a02-converter-1/verify_metadata.py` copy.
Documentation consolidation is recorded in [migration evidence](documentation-migration.json);
[final checks](final-checks.json) confirm preservation, links, private-file ignores
and removal of obsolete references.

Private raw logs, imported solutions and generated problem data remain ignored
under `build/a02-converter-1/`. Do not publish that directory or the real ZIP.
The commands below describe the completed run; use a new output directory when
reproducing conversion. See commands.json for all four preservation commands.

```sh
PCC_ROOT=/tmp/cp-judge-pcc PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m unittest discover -s tests -p test_conversion.py -v
PCC_ROOT=/tmp/cp-judge-pcc PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m tools.pipeline --output build/a02-converter-1/pipeline --real local-packages/gaming-grid.zip
PCC_ROOT=/tmp/cp-judge-pcc PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m tools.verify_install local-packages/gaming-grid.zip build/a02-converter-1/pipeline/converted-3
PCC_ROOT=/tmp/cp-judge-pcc .venv/bin/python -B build/a02-converter-1/verify_metadata.py > build/a02-converter-1/metadata-checks.json
```
