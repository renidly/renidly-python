# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] — 2026-09-26

### Fixed

- `auto_rate_limit` now reads the per-minute limit for enterprise accounts too
  (top-level `limit_per_minute`; `current_tier` is `null` for them). Previously
  an enterprise account whose key did not start with `enterprise-` silently fell
  back to 1 request/minute.
- An undeterminable limit no longer throttles to 1 request/minute: the SDK emits
  a `RuntimeWarning` and skips client-side throttling (server 429s are still
  retried) until a later refresh succeeds.
- The tier endpoint is no longer re-fetched on every request while the limit is
  unknown; it is retried on the refresh interval or after a 429.
- `AsyncRenidly(..., auto_rate_limit=True)` can be constructed outside a running
  event loop on Python 3.9.

### Changed

- `enterprise-` keys no longer require `rate_limit_per_minute`; the fixed limit
  is read from the account. The option remains as an override.

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
