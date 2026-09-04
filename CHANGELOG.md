# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

No changes yet.

## [1.0.0] - Unreleased

### Added
- Core regression coverage for workbook parsing, normalization, pairing, ranking, and export flows.
- Checked-in workbook fixtures for valid, retention-only, malformed, duplicate-header, and ranking-focused release scenarios.
- Headless export regression tests for Excel table export and PNG figure export.
- Module launcher support for `python -m combo_selector`.
- Automated builds for PyPI and the Windows installer when a version tag is pushed.
- Branded Windows executable, installer, shortcuts, and taskbar icon.

### Changed
- Retention, peak-capacity, and elution imports now fail earlier with clearer validation for duplicate headers, missing conditions, and non-numeric cells.
- Ranking updates no longer crash when optional sheets are absent.
- Documentation now points to supported launch commands.
- Package metadata now declares the supported Python versions and complete runtime dependencies.
- The application version is read from installed package metadata, including in the Windows build.
- The packaged application now shows a lightweight Qt splash before importing the full interface and no longer adds an artificial startup delay.

### Fixed

- Optional result columns no longer break ranking when peak-capacity or elution-domain data are absent.
- Undefined correlation matrices no longer break heatmap rendering for a single combination.
- Generated Python cache files are no longer tracked.

### Known limitations

- The Windows installer is currently produced for 64-bit Windows only.
- Release publication requires one-time configuration of PyPI Trusted Publishing in the repository settings.
