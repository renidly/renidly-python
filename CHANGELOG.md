# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] — 2026-07-26

### Added

- PyPI trove classifiers (supported Python versions, typed, license) and
  expanded project URLs.
- Community & contributor docs: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `SECURITY.md`, `LICENSE`, `CHANGELOG.md`, GitHub issue/PR templates, and
  README badges.

_No runtime or API changes._

## [0.1.0] — 2026-07-26

Initial public release.

### Added

- Synchronous `Renidly` and asynchronous `AsyncRenidly` clients with an
  identical, fully-typed surface (ships `py.typed`).
- Single configuration object, `RenidlyConfig`, for all options.
- Four product namespaces off one API key:
  - `data` — people, companies, institutions, skills, job changes (retrieve,
    search, and bulk `enrich_batch`).
  - `live` — people, organizations, opportunities, activities, and discovery
    search.
  - `emails` — verify, find, find-by-URL, reverse, prospects, and bulk
    `verify_batch` / `find_batch`.
  - `account` — balance, tier, enterprise balance, tier ladder, route costs.
- Automatic retries with exponential backoff + jitter on transient failures.
- Transparent pagination via `RenidlyList.auto_paging_iter()`.
- Batch job handles with `.wait()` and streaming `.stream()`.
- Typed exception hierarchy (`RenidlyError` and subclasses) whose messages
  surface the server's field-level detail.
- Dynamic, drill-able response models with `.last_response` HTTP metadata.
- Optional built-in client-side rate limiter (`auto_rate_limit`).

[Unreleased]: https://github.com/renidly/renidly-python/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/renidly/renidly-python/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/renidly/renidly-python/releases/tag/v0.1.0
