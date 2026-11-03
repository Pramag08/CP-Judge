# Local MathJax assets

Exact package: `mathjax@3.2.2`, Apache-2.0, upstream MathJax Consortium.
`package-lock.json` records the npm artifact URL and SHA-512 integrity. It retains
the existing DMOJ MathJax 3 API family; no MathJax 4 migration is implied.

`followup.py bundle` uses A09's pinned Node image and `npm ci --ignore-scripts`.
Only the prebuilt `es5/` distribution (JS components, autoload extensions and
CommonHTML fonts) and unmodified package LICENSE are copied into the private
build context/image, under `/app/resources/vendor/mathjax-3.2.2/`. No node_modules
or generated vendor files are committed. File SHA-256 values are recorded in the
fresh follow-up report, and representative browser rendering must actually load
local extensions and fonts before passing.

The shared profile/content loader, raw statement renderer and Martor preview
loader all resolve this same local bundle. Preview waits for MathJax's real
startup promise before typesetting; it does not fabricate a renderer or swallow
errors. Third-party documentation: https://docs.mathjax.org/en/v3.2/web/hosting.html
