from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from urllib.parse import urlsplit, urlunsplit

from .checker import CheckResult, run_checks
from .config import ConfigError, load_config


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="traxy",
        description="Check HTTP and JSON endpoints from a small JSON configuration.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="run every endpoint check")
    run_parser.add_argument("config", help="path to a Traxy JSON configuration")
    run_parser.add_argument(
        "--format",
        choices=("human", "json"),
        default="human",
        help="output format (default: human)",
    )
    return parser


def _result_payload(result: CheckResult) -> dict[str, object]:
    parsed_url = urlsplit(result.url)
    display_url = urlunsplit(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            "REDACTED" if parsed_url.query else "",
            "",
        )
    )
    return {
        "name": result.name,
        "url": display_url,
        "ok": result.ok,
        "status": result.status,
        "duration_ms": result.duration_ms,
        "errors": list(result.errors),
    }


def _print_human(results: tuple[CheckResult, ...]) -> None:
    for result in results:
        state = "PASS" if result.ok else "FAIL"
        status = "no response" if result.status is None else f"HTTP {result.status}"
        print(f"{state} {result.name} ({status}, {result.duration_ms} ms)")
        for error in result.errors:
            print(f"  - {error}")
    passed = sum(result.ok for result in results)
    print(f"{passed}/{len(results)} checks passed")


def _print_json(results: tuple[CheckResult, ...]) -> None:
    passed = sum(result.ok for result in results)
    payload = {
        "ok": passed == len(results),
        "summary": {"passed": passed, "total": len(results)},
        "results": [_result_payload(result) for result in results],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2

    results = run_checks(config.checks)
    if args.format == "json":
        _print_json(results)
    else:
        _print_human(results)
    return 0 if all(result.ok for result in results) else 1
