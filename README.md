# Polygon → DMOJ compatibility experiment

This repository implements only batch-package conversion and compatibility checks.
It reuses the pinned Problem-Change-Center DMOJ writer with a strict source adapter.
**Successful conversion does not establish successful DMOJ judging.** See
[the compatibility report](reports/compatibility.md) for measured results.

Python 3.10+ and Git are required for conversion; tested here with Python 3.14.4.
From this directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/bootstrap.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m tools.make_fixtures
.venv/bin/python -m tools.pipeline --output build/local-check
# Real package, if available (kept private and ignored):
.venv/bin/python -m tools.pipeline --output build/real-check --real local-packages/gaming-grid.zip
.venv/bin/python -m tools.verify_install local-packages/gaming-grid.zip build/real-check/converted-3
```

Every output directory must be new; existing work is never overwritten.
`PCC_ROOT=/path/to/pinned/checkout` optionally overrides `.deps/converter`.
Tracked modifications or a mismatched converter commit are rejected.
Fixtures are reproducible ZIPs generated from redistributable sources, not exports
from Polygon. The existing `local-packages/gaming-grid.zip` is a real export and
must not be committed or redistributed without its owner's permission.

Actual judging requires a dedicated Linux Docker worker with ptrace/seccomp support.
The following recipe follows DMOJ's upstream runtime image and `SYS_PTRACE` setup:

```sh
docker pull dmoj/runtimes-tier1:latest
runtime_image=$(docker image inspect dmoj/runtimes-tier1:latest --format '{{index .RepoDigests 0}}')
docker build -f Dockerfile.judge --build-arg RUNTIME_IMAGE="$runtime_image" -t cp-judge-compat .
.venv/bin/python -m tools.pipeline --output build/judged --real local-packages/gaming-grid.zip --judge
```

The runner installs each converted problem under `/problems/<short-name>`, then
uses the supported `dmoj-cli test` command. It passes the converted seconds/KiB
limits to DMOJ submissions and compiles testlib checkers via `bridged/type:testlib`.
An unavailable executor reported as `Skipped` makes the run fail, even if DMOJ
exits zero. Every expected case must appear with its expected verdict.
Exit 2 means Docker, image or runtime setup is unavailable; exit 1 means judging
failed (conversion exceptions also exit nonzero). Raw logs and a JSON report remain under the selected output directory.

The image recipe is **NOT TESTED** here: Docker is absent and sudo requires interactive
authentication. An administrator must first install/start Docker and make `docker info`
work for this session, or provide access to a Linux worker.
The runner records the built image ID and runtime-base label, then captures Python,
compiler and installed package versions from an isolated metadata container. It
requires a digest-pinned base and matching judge commit before reporting PASS. Judge source is pinned;
the upstream runtime base/build packages still need a validated immutable lock.
CPP23 requires a suitable compiler in the runtime image; missing CPP23 is a failure,
not permission to downgrade the real checker/reference solution to C++20.

Run this on an isolated worker with no application, credentials or host secrets.
The container receives only installed problem data and a minimal judge configuration,
read-only; no repository/home directory, Docker socket, ports or network are exposed.
It runs as the unprivileged judge user, with a read-only root, resource limits,
`SYS_PTRACE`, no other capabilities, and an ephemeral executable `/tmp`.
A separate worker/VM provides the outer isolation boundary; a container is not a
complete defense against malicious imported native code. Conversion itself does
not compile or run generators, checkers, validators, solutions, or package scripts.

Statements and their assets remain inert files; this does not import them into the
DMOJ website/database or render TeX. The installed problem directory is judge data,
not a complete DMOJ web problem installation. Limits in `init.yml` are integration
metadata: a future site must pass them in submissions, as this test pipeline does.

Only complete, single-problem packages with one standard batch testset, explicit
C++ testlib checker source and HTML/PDF statement are accepted. Complete-group
scoring and earlier group dependencies are supported structurally. Missing answers,
file I/O, interactors, multiple testsets, unknown testset/per-test metadata, unsupported
checker standards, nested local includes and partial checker point protocols are
rejected. Validators/generators/scripts are not run; their behavior is not verified.
Arbitrary C++ semantics cannot be established through static inspection; unusual
checker exit protocols require dedicated judge tests. Milliseconds become seconds;
bytes round up to KiB. Polygon compiler/platform versions are reported, not reproduced.

[Converter source](https://github.com/Albert-Li-Sz/Problem-Change-Center),
[DMOJ setup and sandbox source](https://github.com/DMOJ/judge-server#running-a-judge-with-docker),
[attribution](THIRD_PARTY.md), [fixture expectations](fixtures/README.md).
