# Traxy

[![CI](https://github.com/traxy111/Traxy/actions/workflows/ci.yml/badge.svg)](https://github.com/traxy111/Traxy/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Traxy is a small, dependency-free command-line monitor for HTTP endpoints. It
checks expected status codes and optional JSON fields, produces readable or JSON
output, and returns CI-friendly exit codes.

It is designed for maintainers who want a transparent health check without
running a monitoring server or adopting a large SDK.

## Features

- Check any HTTP or HTTPS endpoint with a configurable timeout.
- Assert an exact HTTP status code.
- Inspect redirect responses without following them automatically.
- Assert values at dotted JSON paths such as `service.version`.
- Use human-readable output locally or structured JSON in automation.
- Exit with `0` when all checks pass, `1` on check failures, and `2` for invalid
  configuration.
- Run with Python's standard library only.

## Install

From a checkout:

```bash
python -m pip install -e .
```

Or run the project with [uv](https://docs.astral.sh/uv/):

```bash
uv run traxy run examples/traxy.json
```

## Configuration

Create a JSON file:

```json
{
  "checks": [
    {
      "name": "Traxy repository",
      "url": "https://api.github.com/repos/traxy111/Traxy",
      "timeout": 10,
      "expect": {
        "status": 200,
        "json": {
          "full_name": "traxy111/Traxy",
          "private": false
        }
      }
    }
  ]
}
```

Run all checks:

```bash
traxy run traxy.json
```

Example output:

```text
PASS Traxy repository (HTTP 200, 214 ms)
1/1 checks passed
```

For machine-readable output:

```bash
traxy run traxy.json --format json
```

Query-string values are replaced with `REDACTED` in JSON output. Configuration
URLs must not contain embedded usernames, passwords, fragments, or whitespace.

## Use in CI

Add a configuration file to your project and call Traxy after a deployment:

```yaml
- name: Verify deployed endpoints
  run: uv run traxy run traxy.json --format json
```

Traxy never needs credentials for public endpoints. If your workflow injects
private URLs or headers around Traxy, keep those values in your CI secret store
and never commit them.

## Development

```bash
uv sync --dev
uv run pytest --cov=traxy --cov-report=term-missing
uv run ruff check .
```

The tests use an in-process local HTTP server and do not rely on public network
services.

## Project status

Traxy is an early-stage project. Version `0.1.0` intentionally focuses on a
small, auditable feature set. See the [changelog](CHANGELOG.md) and open an issue
for a concrete use case before proposing a large feature.

## Contributing and security

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening
a pull request. Please report security concerns as described in
[SECURITY.md](SECURITY.md), not in a public issue.

## License

MIT License. See [LICENSE](LICENSE).
