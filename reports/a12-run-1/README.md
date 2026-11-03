# A12 — custom-input Run investigation

**COMPLETE — source-grounded adapter design, no custom-run implementation.**
[Contract](../../docs/contracts/custom-input-run.md).

`python3 -B reports/a12-run-1/inspect.py` exited **0**. Evidence:
[pins/source SHA-256/observations](evidence.json), [exact commands/exits](commands.json).
Pinned files match Git objects. Native receiver has five recognized operation
names; an isolated AST-extracted call logs the proposed custom packet as unknown.
The native control POST handler returns 404 for `/run`. AST inspection confirms
real TracedPopen sandbox/resource/stdin/stdout/stderr arguments. These checks use
simple test objects and no dependency imports, sockets, DB, compiler or sandbox;
they establish extension points and unsupported routes, not live compatibility.

Decision: dedicated authenticated Run broker/adapter around actual DMOJ executor
constructor → launch → communicate APIs, in fresh isolated jobs without official
problem mounts/checkers/bridge/database access. Specify byte/time/memory/compiler/
output limits, quotas, official-job reservation/preemption, owner/session scope,
result states, encoding, cleanup and retention. Native compilation requires outer
memory/wall/process caps; output-limit exceptions do not return captured prefixes.

No Phase A design blocker. New adapter, sandbox probes and fairness/capacity checks
remain E07/E08/G12; actual custom-input execution and browser/bridge compatibility
are **NOT TESTED**. Conversion/judging/A09 startup were not rerun. No dependency
or source patch, service start, commit or push.
