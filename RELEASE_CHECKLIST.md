# 2DComboSelector 1.0.0 release checklist

This checklist separates automated validation from the manual scientific and user-interface checks required before publishing the first stable release.

## One-time repository configuration

- [ ] Protect `main` and require the `Core Validation` check.
- [ ] Create a GitHub environment named `pypi`.
- [ ] Configure a PyPI Trusted Publisher for this repository, workflow `release.yml`, and environment `pypi`.
- [ ] Confirm the copyright holder used in `LICENSE`.

## Release candidate validation

- [ ] All automated tests pass on every supported Python version.
- [ ] The wheel and source distribution pass `twine check`.
- [ ] Install the wheel in a clean environment and launch with `combo-selector`.
- [ ] Launch the Windows installer on a clean Windows computer.
- [ ] Confirm that Start Menu and optional desktop shortcuts work.
- [ ] Run the trusted full-format and retention-only workbooks through the GUI.
- [ ] Verify normalization, pair generation, metric calculation, grouping, final ranking, and export.
- [ ] Confirm that malformed workbooks produce understandable user-facing messages.
- [ ] Review the numerical results of the regression fixture against the intended scientific method.
- [ ] Update screenshots and user documentation if the interface has changed.
- [ ] Review the `1.0.0` section of `CHANGELOG.md` and document known limitations.

## Publication

- [ ] Merge the release PR into `main` only after required checks pass.
- [ ] Create and push the annotated tag `v1.0.0` from the verified merge commit.
- [ ] Confirm that the GitHub Release contains the Windows installer, wheel, and source distribution.
- [ ] Confirm that `2dcomboselector==1.0.0` is available from PyPI.
- [ ] Perform a final clean install from PyPI and launch the application.

## Rollback rule

If a publication check fails, do not reuse the `1.0.0` version number on PyPI. Fix the problem and publish a patch release such as `1.0.1`.
