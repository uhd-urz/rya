# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.38] - 2026-06-08

This release brings some type annotation improvements and a quick fix for breaking changes to a dependency.

### Added

- Add `force_reregister` parameter to `ConfigMaker.add_model` method.

### Changed

- Pin dependency typer to `<0.26` to avoid breaking click's behavior. See
  issue: https://github.com/uhd-urz/rya/issues/3.

## [0.2.37] - 2025-02-12

This release refactors and breaks some APIs of `styles.BaseFormat`.

| Old                         | New                                 |
|-----------------------------|-------------------------------------|
| `supported_formatters`      | `get_all_supported_formatters`      |
| `supported_formatter_names` | `get_all_supported_formatter_names` |
|                             | `get_supported_formatters`          |
|                             | `get_supported_formatter_names`     |

## [0.2.24] - 2025-11-07

The third beta release of Rya that replaces the old AGPL license with the permissive MIT license. Thanks
@alexander-haller!

## [0.2.23] - 2025-11-07

Second beta release of Rya with more refactors and improvements.

## [0.2.13] - 2025-10-31

Initial beta release of Rya. Rya is now capable of bootstrapping a new Python CLI application that shares the same
capabilities as elAPI. 

