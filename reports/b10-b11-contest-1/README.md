**B10/B11 PASS — one agent; stopped before B12.** Private native contest
`b10b11local1`, temporary ordinary accounts `b10tmpa`/`b10tmpb`, one unchanged private
CPP23 problem. Browser checks denied anonymous/non-allowlisted contest access and
problem access before joining; both native joins then exposed the problem and
produced separately owned official submissions6/7. Both late entrants retain the
same original server start/end, with no individual duration.

Manual calculation uses persisted server receipts, never browser clicks or grading
completion: S=`2026-10-29T13:53:53.494549+00:00`; B's AC9 receipt is
`14:09:54.700307+00:00`, A's AC10 is `14:09:54.703466+00:00` on the same date.
Both elapsed times floor to961s; each has one prior WA:961+1200=**2161s (36:01)**.
CE8 adds0; later WA11 adds0. Native case points remain separate from solved count.

| Participant / actual sequence | Solved expected / actual | Penalty seconds expected / actual | Rank expected / actual |
| --- | --- | --- | --- |
| B: WA6 → AC9 | 1 / 1 | 2161 / 2161 | 1 / 1 |
| A: WA7 → CE8 → AC10 → later WA11 | 1 / 1 | 2161 / 2161 | 1 / 1 |

Tied display order is B then A, by entry IDs1 then2. Stock ICPC originally ranked
these equal totals1,2 using fractional last-solve time, and its unsolved tied-row
order also differed. Fixed with the planned registered `cpjudge_icpc_v1` extension:
full-AC-only native contest credit, exact failure filtering, whole seconds per
problem, neutral tiebreaker and stable ranking query. Existing formats retain their
behavior. Metadata-only migration0154 registers the added choice; consistency passes.
Native idle guards were used for the necessary code reload; this is not B12's
restart/persistence acceptance. Existing submissions were recomputed without rejudge;
AC9/10 were not repeated. Actual post-fix WA11 verified the live native callback hook
and unchanged standings. All515 executed case callbacks match stored statuses and
points; CE has0 cases,103 unexecuted. No skipped cases counted as passes.

Evidence: [before fix](results-20261029T141128278450Z.json), [final server/manual/results](results-20261029T142933224089Z.json),
[actual final browser](after-browser-20261029T142752694221Z.json), [18 focused scoring checks](scoring-checks.json),
[patch identity/migration](scoring-install.json), [88-model preservation](preserve.json),
[exact commands/exits/private log paths](commands.json). Source pin remains
`604d60cfd764bc708b04ffd75b715a5398b91f8b` plus the recorded local patches.

Command prefix: `.venv/bin/python -B deploy/site-local/contest_journey.py`.
Final `setup`, `ce`, `pair`, `install-scoring`, `checks`, `after`, `collect`,
`standings` and `preserve` commands exited0. B10's final parser failed after its
successful submissions; corrected read-only collection completed acceptance without
resubmission. Earlier mount/confirmation failures created no submissions. Preservation
collector's primary-key assumption was corrected and rerun read-only. Failed/raw
browser/compiler logs, DOM and screenshots stay ignored under
`build/b10-b11-contest-1/`; credentials are in its mode0600 `accounts.json`.

Existing accounts/passwords/submissions, statement/problem files, worker configuration,
images and sandbox restrictions were preserved. Only named fixture rows were added;
fixture retained for later checks.18 focused checks cover acceptance guards, failure
codes/CE, per-problem rounding, receipt/ID ordering, ignoring later attempts and
recomputation on constructed authoritative replacements. Non-tie solved/penalty
ordering uses the real SQL ranking provider with temporary derived-score fixtures
rolled back;1,1,3 uses native ranker fixtures. The browser proves a real two-entrant
1,1 tie, not a live three-entrant competition. Admission/deadline races, registration
policies beyond this native allowlist, operational rejudge, recovery/load and B12
persistence remain untested. No UI redesign, learning document, commit or push.
