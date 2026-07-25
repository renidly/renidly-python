# Security Policy

We take the security of the Renidly Python SDK and our users seriously.

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, report them privately using one of:

- **GitHub Security Advisories** — [open a private report](https://github.com/renidly/renidly-python/security/advisories/new) (preferred).
- **Email** — [support@renidly.com](mailto:support@renidly.com).

Please include:

- a description of the issue and its impact,
- steps to reproduce (a minimal proof of concept if possible),
- affected version(s).

We'll acknowledge your report, investigate, and keep you updated on the fix and disclosure timeline. We're happy to credit reporters who wish to be named.

## Supported versions

The SDK is pre-1.0. Security fixes are released on the **latest** published version. Please keep up to date with `pip install --upgrade renidly`.

## Handling API keys

The SDK never logs your API key. When integrating:

- Load keys from the environment or a secrets manager — never hard-code them.
- Do not commit `.env` files or keys to source control.
- Rotate keys promptly if one may have been exposed.
