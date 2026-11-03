# B06 — real private statement in native DMOJ

**PASS for B06 rendering/access/sanitization; judging NOT RUN.**
[Presentation hashes](presentation.json), [commands/exits](commands.json),
[independent review](review.json). Final `browser-*.json` and `preservation-*.json`
are successful actual runs, not CLI or mocked browser evidence.

Problem: http://127.0.0.1:8000/problem/pv000000000000000001
Private gaming-grid revision1 remains the B05 code, limits and immutable judge
manifest. The selected existing ordinary participant now has only native Problem
tester access; no staff/edit/global-private permission or public visibility was
granted. Anonymous problem and stylesheet access both return404.

The English package HTML contains2 script tags (including remote MathJax),1
relative CSS link and no images. The bounded adapter selects only the statement
body, strips executable/head/event/URL content, retains allowed structural tags
and classes, normalizes sample lines, and translates all30 Polygon math expressions
for existing local MathJax3.2.2. TeX commands are restricted to the selected subset
cdot/le/dots; raw native math forms, split-node command assembly and unsupported
commands fail closed. No raw package script or external math resource executes.

The referenced CSS is parsed with locked tinycss2, scoped under `.b06-imported`,
and restricted to safe property/value tokens: no at-rules, functions, URLs or
external resources. It is stored outside static/media, served only by a fixed-name
permission-checked native route with private/no-store and nosniff headers.
The original stylesheet/assets remain unchanged on the read-only worker mount.

Native Markdown misparsed the compact source HTML (literal closing tags and lost
math delimiters were caught in Chromium). A narrow filter in the existing native
problem template now renders **only** this sanitized fragment after its full SHA256
matches the private presentation receipt. No general full-markup flag was enabled;
unknown content fails closed. Native ProblemMixin access and page layout remain.
Private receipt binds package SHA and the original judge-manifest digest. B05's
operator verifier now accepts only this separate receipt-bound presentation while
still checking all immutable judging fields/files. It never rewrites the original
installation registry or data to add statement content.

One pre-existing Martor/Semantic UI Google Fonts import appeared only on the real
problem page. Removed only that import from source and collected semantic.css;
existing fallback fonts/layout remain, dependency pins unchanged. All actual
statement CSS/math/font requests are local and return200. The browser's local-only
policy still blocks legacy Gravatar decoration; full-site offline operation is not
claimed. No production warning was silenced.

Actual final Chromium acceptance: exact ordered30 TeX expressions, real typesetting
without math errors/duplicates, legend/constraints/input/output/note text and both
sample blocks match package HTML; native navigation/sidebar/footer retained.
Screenshot visually inspected. Real login and logout used the native forms.
The granted participant received219 denied hidden-data/source/static/traversal
responses, including every103 input/output path; tester access does not grant
test-data/edit rights. No test archive, answer, checker/reference source or PDF/TeX
source was exposed by the stylesheet route. Raw screenshots, DOM, package text and
browser failures stay under ignored build/b06-statement-1/.

Commands (repository root), final exits0:

```sh
python3 -B deploy/site-local/problem_journey.py snapshot
.venv/bin/python -B deploy/site-local/problem_journey.py prepare
.venv/bin/python -B deploy/site-local/problem_journey.py install
.venv/bin/python -B deploy/site-local/problem_journey.py browser
.venv/bin/python -B deploy/site-local/problem_journey.py preserve
env CPJ_PROBLEM_REPORT=/home/pramag/Documents/CP-Judge/reports/b06-statement-1 .venv/bin/python -B deploy/site-local/problem_install.py verify
```

Prepare's focused adversarial HTML/CSS/TeX checks ran in the locked website
environment. No packages installed and no expensive judging/converter suite rerun.
Worker verification rechecked all103 source/worker pairs and21 file hashes, checker,
header, sample and15 assets, CPP23/2s/262144KiB, confirming installed bytes unchanged.
Precise baseline covers88 model/relation sets with full datetime microseconds:
only description/tester relation and normal native login/access fields changed;
passwords, other existing domain data and worker authentication stayed exact.
Owned browser sessions were deleted via the configured cache+DB session backend.

Failed exploratory runs remain: host Python lacked defusedxml (used the existing
venv); native Markdown math failure; a browser check initially counted trusted
MathJax-generated styles as unsafe; native font import; hidden logout dropdown.
Final relevant checks passed after correction. No failure is counted as a pass.

Limitations: this is the selected HTML/strict TeX subset, not general author import,
PDF rendering, publication or A11 readiness enforcement. No submissions in B06.
Next authorized task in this bundle: B07 only after B06 review/status recording.
No redesign, learning document, commit or push.
