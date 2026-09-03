# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Core regression coverage for workbook parsing, normalization, pairing, ranking, and export flows.
- Checked-in workbook fixtures for valid, retention-only, malformed, duplicate-header, and ranking-focused release scenarios.
- Headless export regression tests for Excel table export and PNG figure export.
- Module launcher support for `python -m combo_selector`.

### Changed
- Retention, peak-capacity, and elution imports now fail earlier with clearer validation for duplicate headers, missing conditions, and non-numeric cells.
- Ranking updates no longer crash when optional sheets are absent.
- Documentation now points to supported launch commands.

## [1.0.0] - Planned release gate

`v1.0.0` should only be tagged after all of the following are true:

- workbook import succeeds for trusted retention-only and full-format examples
- malformed workbooks fail with clear user-facing errors
- ranking and pair-generation regressions stay green in CI
- export of tables and figures works in a clean installed environment
- startup works from both `combo-selector` and `python -m combo_selector`
- branch protection requires the `Core Validation` workflow
- release notes summarize user-visible fixes and remaining known limitations
