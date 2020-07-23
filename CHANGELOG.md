# Changelog

Documentations of changes to the source code and the project.

## [Unrelease]

## [0.1.3] - 2020-07-16

### Changed
- Publish workflow setup correctly (finally)
- Runs `pytag -t develop pytagged` to remove development code before publish (correctly this time)


## [0.1.2] - 2020-07-16

### Changed
- Setting up publish workflow:
    - Triggered on non-draft release (github) is created
    - Runs `pytagged -t develop` on source code before building & publishing

## [0.1.1] - 2020-07-16

### Changed
- Update README.md to provide usage examples and explanations

### Added
- Multiple files: recursively match all `.py` files in the directory & subdirectories and work on all of them
- Ignore already commented lines, triple quote blocks and docstrings
- Triple quoted strings can be commented out using block tags
- Different modes: verbose, benchmark and printonly
    - verbose prints more stuff
    - benchmark performs a benchmark of n runs, and prints out stats about time taken
- CI stuffs:
    - Test for the dev and release versions
    - Add workflow to publish to Pypi registry

## [0.1.0] - 2020-07-16

### Added
- Basic functionality for a single file:
    - Inline tag for commenting out a single lines
    - Block tag for commenting out a block of code

## [0.0.1] - 2020-07-16
### Added
- Template README
- setup.py

[unreleased]: https://github.com/ntn9995/pytagged/compare/v0.1.3...HEAD
[0.1.3]: [https://github.com/ntn9995/pytagged/compare/v0.1.2...v0.1.3]
[0.1.2]: https://github.com/ntn9995/pytagged/compare/v0.1.1...v0.1.2
[0.1.1]: [https://github.com/ntn9995/pytagged/compare/v0.1.0...v0.1.1]
[0.1.0]: [https://github.com/ntn9995/pytagged/compare/v0.0.1...v0.1.0]
[0.0.1]: https://github.com/ntn9995/pytagged/releases/tag/v0.0.1