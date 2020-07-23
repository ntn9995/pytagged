# Changelog

Documentations of changes to the source code and the project.

## [Unreleased]

## [0.2.0] - 2020-07-23

### Added
- Exclude option: Users can now exclude files & directories that match against certain patterns using the -x/--exclude options. By default, pytagged ignores paths that match against any of these patterns (taken from flake8's default exclusion):
    - .svn
    - CVS
    - .bzr
    - .hg
    - .git
    - __pycache__
    - .tox
    - .eggs
    - *.egg
- Extend exclude option: Users can also use the -xt/--extend flag to add more patterns to the default excluded patterns (or provided patterns). The final set of excluded patterns will be the union set of the -x and -xt sets.
- Config file: Every command line flag (except for -cf/--config) has a corresponding option configurable in a .ini file format. By default, pytagged looks for the `pytagged.ini` file in the working directory. The user can also provide a specific config file using the -cf/--config flag. The config file can be used in conjunction with the command line arguments, although the latter take precedence. See the README for example usage.

### Changed
- bechmark mode (-b/--benchmark) now prints out elapsed time of these individual phases:
    - opening file
    - parsing the files and generating replacement
    - writing the replacement
    - closing the file
- verbose is now verbosity (-v/--verbosity) and is no longer mutually exclusive with the benchmark and printonly modes.

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

[unreleased]: https://github.com/ntn9995/pytagged/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/ntn9995/pytagged/compare/v0.1.3...v0.2.0
[0.1.3]: https://github.com/ntn9995/pytagged/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/ntn9995/pytagged/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/ntn9995/pytagged/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ntn9995/pytagged/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/ntn9995/pytagged/releases/tag/v0.0.1