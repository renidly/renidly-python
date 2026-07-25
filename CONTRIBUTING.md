# Contributing to the Renidly Python SDK

First off — **thank you!** Contributions of every size are welcome: bug reports, docs, tests, and features. This guide gets you productive in a couple of minutes.

## Ways to contribute

- 🐛 **Report a bug** — open an [issue](https://github.com/renidly/renidly-python/issues) with a minimal reproduction.
- 💡 **Request a feature** — open an issue describing the use case.
- 📖 **Improve docs** — the README, docstrings, and examples can always be clearer.
- 🧑‍💻 **Send a pull request** — see below.

## Development setup

Requires **Python 3.9+**.

```sh
git clone https://github.com/renidly/renidly-python.git
cd renidly-python

python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

pip install -e ".[dev]"              # installs the package + dev tools
```

## The three checks (CI runs exactly these)

```sh
ruff check src tests                 # lint + import sorting
mypy src/renidly                     # static types
pytest                               # tests (fast; fully mocked, no network)
```

All three must pass before a PR can merge. Auto-fix lint issues with `ruff check --fix src tests`.

## Project layout

```
src/renidly/
  _client.py       # Renidly / AsyncRenidly (the public clients)
  _config.py       # RenidlyConfig
  _transport.py    # HTTP engine: retries, response handling, error mapping
  _errors.py       # exception hierarchy
  _models.py       # response models
  _pagination.py   # list + auto-paging
  _batch.py        # batch job handles
  _ratelimit.py    # optional client-side rate limiter
  resources/       # the public method surface (account, data, emails, live)
  types/           # typed request-parameter definitions
tests/             # mocked unit tests (respx)
```

The core (`_transport`, `_models`, `_pagination`, `_batch`) is the stable machinery; the `resources/` files are thin, uniform wrappers over it. New endpoints usually mean a small addition to a resource file plus a test.

## Pull request guidelines

1. **Fork** the repo and create a branch off `main` (`git checkout -b fix/clear-error-message`).
2. **Keep it focused** — one logical change per PR.
3. **Add a test** for any behavior change (we use `respx` to mock HTTP — no network in the test suite).
4. **Document it** — every public class and method has a docstring with a short example; match that style.
5. Run the three checks locally and make sure they're green.
6. Open the PR with a clear description of *what* and *why*.

We aim to review PRs promptly. Maintainers may request changes or tweak details before merging.

## Coding standards

- **Types everywhere** — public methods are annotated so they autocomplete in users' editors. Prefer real types over `Any`.
- **Docstrings are required** on public classes/methods: one-line summary, a note on how it works, and an example.
- **Line length** is relaxed for the one-line-per-endpoint resource files; everything else follows `ruff` defaults.
- **Keep the surface consistent** — mirror existing method names and signatures (sync and async stay in lockstep).

## Reporting security issues

Please do **not** open a public issue for security vulnerabilities. See [SECURITY.md](SECURITY.md).

## Code of Conduct

By participating you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
