This repository is pramag08/CP-Judge, the judging and problem-import
component for SecureExam.

We want to reuse DMOJ and existing open-source conversion tools.
Our immediate goal is to verify actual Polygon-to-DMOJ compatibility.

Real package: local-packages/gaming-grid.zip

Inspect the repository and existing instructions first.

Create or update a concise AGENTS.md covering:
- Reuse upstream projects and pin tested versions/commits.
- Preserve existing work and upstream attribution.
- Keep local-packages/, extracted private problems, secrets, and
  private judging logs out of Git.
- Conversion success and judging success are separate outcomes.
- Never claim tests passed unless they actually ran.
- Keep the scope limited to importing and judging.

Then implement the smallest working end-to-end test:

1. Inspect the Polygon package without executing its contents.
   Identify its checker, test structure, limits, and scoring.

2. Evaluate the existing converter:
   https://github.com/Albert-Li-Sz/Problem-Change-Center
   Inspect its license and Polygon/DMOJ adapters before adopting it.
   Reuse it if suitable; explain concrete gaps otherwise.

3. Convert this real package and run its reference solution through
   the actual DMOJ judging engine in an isolated environment.
   Also run a deliberately wrong solution with a verified expected
   failure. Do not replace DMOJ with a homemade output comparison.

4. Provide repeatable setup and test commands, pinned dependencies,
   and a sanitized compatibility report.

Success requires correct reference-solution acceptance and rejection
of the known-wrong solution, with checker and limits preserved.

Keep unsupported features explicitly marked unsupported.
If execution is blocked, report the exact blocker and completed work.
Proceed through implementation and testing; do not stop at a plan.

Do not build the frontend, lockdown system, or full contest deployment.
Do not commit the private package or push changes yet.