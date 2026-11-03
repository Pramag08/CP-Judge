# A11 — dispatch/version investigation

**COMPLETE — design and isolated source semantics only.**
[Contract](../../docs/contracts/problem-version-dispatch.md).

Command: `python3 -B reports/a11-dispatch-1/inspect.py` exited **0**. The script
checks selected checkout files against immutable Git objects and records SHA-256
in [evidence.json](evidence.json); exact subprocess commands/exits are in
[commands.json](commands.json). It executes the actual AST-extracted upstream
path/cache/advertisement functions using temporary synthetic files, plus native
`can_judge` with simple in-memory attributes. Four observations and six selection
cases passed. Dependency imports/DB/network are deliberately absent, so this is
not a bridge integration test or sandbox test.

Observed: duplicate code prefers first root; clearing root-list cache leaves
existing code-root mapping cached; changed bytes can retain the same advertisement;
new codes advertise independently. Native selection checks code/executor/target,
with the explicit target bypassing the handler's disabled check. Native scheduler
tiers/load/queues, cache keys, data loading, result IDs and rejudge behavior were
inspected, not executed end to end.

Decision: immutable native Problem/code per revision; authenticated deployment
manifest receipts outside the wire protocol; readiness predicate inside both
bridge scheduling paths; frozen limits; explicit authoritative attempt mapping.
No invented native version/hash/pool field. No new blocker to design completion.
Implementation checks remain B03/B04/B09/C10/C11/F10/F11/G04/G09.

Conversion **NOT RUN**; actual judging **NOT RUN**; website-to-worker compatibility
**NOT TESTED**. A02/A03/A09 evidence/pins were inspected and preserved, without
rerunning expensive checks. No source patch, service start, commit or push.
