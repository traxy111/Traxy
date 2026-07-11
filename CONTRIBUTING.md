# Contributing to Traxy

Thank you for helping improve Traxy.

## Before opening a change

1. Search existing issues and pull requests.
2. Open an issue for behavior changes or new features.
3. Keep proposals narrow and include a real endpoint-checking use case.

## Development workflow

Traxy uses test-driven development. Add or update a failing test before changing
the implementation.

```bash
uv sync --dev
uv run pytest --cov=traxy --cov-report=term-missing --cov-fail-under=80
uv run ruff check .
```

Pull requests should:

- include tests for success and failure behavior;
- preserve the documented exit-code contract;
- avoid adding runtime dependencies without a clear need;
- update README examples or the changelog when user-visible behavior changes;
- contain no credentials, private endpoints, or copied production data.

By contributing, you agree that your contribution is licensed under the MIT
License.

