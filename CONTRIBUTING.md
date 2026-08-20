# Contributing

Thank you for helping improve the Universal Baseball Model.

## Workflow

1. Read [`docs/project-status.md`](docs/project-status.md) and the contract for
   the component you intend to change.
2. Create a focused branch from current protected `main`.
3. Keep frozen v1 decisions and outputs unchanged unless a concrete
   implementation contradiction is demonstrated and documented.
4. Run the same checks as pull-request CI:

   ```bash
   python -m pip install -e ".[dev]"
   python -m ruff check src scripts tests
   python -m pytest
   ```

5. Open a pull request that identifies affected contracts, provenance, tests,
   and any numerical changes.

Do not commit raw or bulk third-party source data, credentials, generated
scratch outputs, or mutable live-source responses. Follow
[`config/source-policies.json`](config/source-policies.json) and
[NOTICE.md](NOTICE.md) for attribution and redistribution boundaries.

Report security vulnerabilities privately according to
[`.github/SECURITY.md`](.github/SECURITY.md), not in a public issue.
