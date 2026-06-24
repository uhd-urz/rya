# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.41] - 2026-06-24

### Added

- Add configuration locations to `config meta` output 

## [0.2.40] - 2026-06-24

This release introduces the `config` plugin (different from the `config` layer), some general improvements, and bug
fixes. The `config` plugin is a generalization of the `elapi show-config` command. Unlike the `elapi show-config`,
`config show` is more powerful and completely automated.

### Added

- Add the `config show` command that lists all detected configuration fields read from the files
- Add support for user provided options to specify displayed configuration list: `--filter` and `--include`
- Add shortcut flags to display list: `--long/-l` and `--short/-s`
- Add flag to show/hide display table border: `--border/-B`
- Allow masked configuration secret strings to paritally reveal via `ConfDescDefinition`
- Add the `config meta` command that shows meta information about the running Rya app
- Add `_meta` field to the cache model to store app-internal information; add `update_meta_cache` method to modify the
  `_meta` field

### Changed

- Rename `pre_utils/` layer to `kernel/`
- Remove public layer `core_validators/`; move important validation helper method to `kernel/`
- Consolidate app path definitions into model instance `app_locations`
- Set default Typer `rich_markup_mode` value to `rich`
- Improve the cache model: The cache model can now be extended with `BaseCacheModel`

### Fixed

- Various type annotation issues
- Fix rich-click still showing a warning (#5)

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

