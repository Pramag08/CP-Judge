# B04 — native problem installation mapping

**PASS for B04 mapping/source inspection only.** [Exact mapping](mapping.json),
[commands/exits](commands.json), [independent review](review.json).
No problem/database installation or program submission was performed in B04.

Source pins: site `604d60cfd764bc708b04ffd75b715a5398b91f8b`, worker
`1245dc4158dbb9e906c4c103e1ea939e012ee79b`, converter
`41ce3afcedf6c02793b308ba2e6ddb2ea5f82134`. Actual site source hashes match the
selected checkout; actual pinned worker source was inspected through its running
container. AGPL/MIT attribution remains unchanged. `/tmp` converter/judge checkouts
are absent; reuse A02's already-converted output after fresh independent ZIP vs
conversion verification, without rerunning conversion or changing dependencies.

## Identity, paths and metadata

Display identity `gaming-grid`; operator revision1 uses native code
**`pv000000000000000001`** (20 lowercase alphanumeric characters). This is an opaque
18-digit operator revision, not a truncated hash. Full source-package SHA256 and
canonical deployment-manifest SHA256 remain in an ignored immutable installation
registry. The manifest covers every converted relative file, size/hash, converter
pin and frozen site fields. A revision/code already bound to different bytes or
metadata is rejected; no silent replacement. New versions require an explicitly
different revision and native Problem/code; no display-alias engine is implemented.

Native `Problem` row: source title, private (`is_public=False`), manually managed,
blank description until B06, required native category, allowed languages exactly
CPP23. No ProblemData/ProblemTestCase compiler is used: it would regenerate/overwrite
configuration and its stock checker choices do not represent bridged/testlib.
The current database has no categories; B05 creates only native ProblemGroup
`localpolygon` / `Private Polygon imports` if absent and refuses conflicting metadata.
No statement HTML or reference source is installed in the website or static/media.

Worker path: existing read-only `/problems/<native-code>/`, backed by ignored
`build/b03-worker-1/problems/<native-code>/`. All converted files stay private:
`init.yml`, `data.zip`, CPP23 testlib checker/header, one sample pair and15 inert
statement/support assets. Original reference source stays only in the ignored
source package. No worker image/config/mount/compiler change is needed. Stage
beside the final path on the same filesystem, verify full manifest and package,
make files/directories read-only, then atomic rename. Ordinary repeat installation
must compare files AND ORM metadata, retain the same PK/code, and change nothing.

## Limits and native request values

| Property | Source/conversion | Installed site value | Expected bridge→worker field |
| --- | --- | --- | --- |
| Time | 2000ms →2.0 seconds | `Problem.time_limit=2.0` | `time-limit:2.0` |
| Memory | 268435456bytes →262144KiB | `Problem.memory_limit=262144` | `memory-limit:262144` |
| Language | checker/reference require CPP23 | allowed languages exactly existing `CPP23` | `language:CPP23` |
| Short circuit | converter preserves false | `Problem.short_circuit=False` | `short-circuit:false` |
| Identity | revision1 + full immutable digests | unique code above | `problem-id:<code>` |

Source inspected: `judge/models/problem.py`, `judge/models/submission.py`,
`judge/judgeapi.py`, `judge/bridge/judge_handler.py`; worker `packet.py`, `problem.py`,
`judgeenv.py`, `judge.py`, `checkers/bridged.py`. Hashes and actual worker limit
semantics are in mapping.json.

`judge_submission()` initially sends submission-id, problem-id, language, source,
optional judge-id and priority. It **does not send limits from init.yml**.
Bridge `get_related_submission_data()` rereads Problem limits, then any matching
LanguageLimit override; `submit()` sends the limits unchanged with short-circuit
and native meta (pretests-only/in-contest/attempt-no/user/user-notes). The worker
constructs its Problem using those request limits. B05 must assert no overrides,
exact CPP23 mapping and ORM/init agreement, without creating a Submission or
sending submission-request. Actual emitted submission packets remain B07 evidence.

## Cases, checker, samples and scoring

All103 source input/output pairs remain active in original order1…103, including
sample1; no sample is removed from judging. Bridged checker is testlib with
`files=[checker.cpp,testlib.h]`, `lang=CPP23`; source/header bytes must match ZIP.
One sample pair and all15 statement/support assets are verified byte for byte.
No generators, validators, checkers, references or submissions are executed here.

Converted ungrouped cases carry one point each (raw total103); no groups or
dependencies exist in this package. Native `Problem.points=103`, `partial=True`
preserves this supported raw case-point sum in standalone website results:
upstream normalizes raw points/total by Problem.points. This is not a claim about
Polygon contest scoring. Future B10's **ContestProblem** must separately enforce
the required full-acceptance one-point ICPC preset; no contest exists here.
Checker partial-point protocols remain unsupported as in the converter.

A11's verified manifest/probe/boot-bound readiness receipt, bridge pool predicate,
author publication, correction attempts and dispatch-time immutability enforcement
remain later work. Installation/advertisement alone cannot satisfy those gates;
keep this imported revision private and unassigned. The operator procedure freezes
and verifies its own revision; it does not claim to prevent privileged external edits.

Command: `.venv/bin/python -B deploy/site-local/problem_install.py plan` exited0.
It independently rechecked all103 pairs/checker/header/assets against source ZIP,
matched A02's recorded source hash/results and inspected native runtime/source.
No previous dependency milestone was rerun. B05 follows only after this mapping
is recorded/reviewed. Judging and statement rendering NOT TESTED. No commit/push.
