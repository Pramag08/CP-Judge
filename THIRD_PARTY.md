Dependency pins are in `dependencies.json`; Python conversion dependencies are in
`requirements.txt`. Converter and judge sources are fetched separately, not copied.

- Problem-Change-Center, Albert_Li, MIT, commit `41ce3afcedf6c02793b308ba2e6ddb2ea5f82134`.
  We import its `runner/package_ir.py` model and `runner/package_adapters.py` DMOJ
  writer/validator. Its LICENSE remains in the fetched checkout.
- DMOJ judge-server, DMOJ Team, AGPL-3.0-or-later, commit
  `1245dc4158dbb9e906c4c103e1ea939e012ee79b`. Runs as a separate program in the
  proposed judge image. Source and license are retained inside that image at `/judge`.
- testlib, Mike Mirzayanov, MIT, commit `3bf5ba5aca6007bf8dcde6d00949ec3116ee3cc7`.
  Only its checker header is vendored with LICENSE under `fixtures/testlib/`.
- defusedxml 0.7.1 (PSF license), PyYAML 6.0.3 (MIT).

The judge image recipe pins judge source but currently follows upstream's mutable
runtime base and unpinned build dependencies. Record the base digest and installed
package versions for each executed judge run. Container image build and execution
have not been verified in this workspace.

Audit-only dependency: KisuraOP/polygon2hydro at
`93aca21db49131baa0ca3077d6fec037ac52b5e6`, MIT. Not used by the adapter. To repeat:
clone its repository, check out that commit, then run
`python -m tools.audit_upstream /path/to/polygon2hydro` with the converter configured.
