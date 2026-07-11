from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .config import Check

_MAX_BODY_BYTES = 1_048_576
_MISSING = object()


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, ARG002
        return None


_OPENER = build_opener(_NoRedirectHandler())


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    url: str
    ok: bool
    status: int | None
    duration_ms: int
    errors: tuple[str, ...]


def _resolve_json_path(payload: object, path: str) -> object:
    current = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return _MISSING
        current = current[part]
    return current


def resolve_json_path(payload: object, path: str) -> object | None:
    """Return a value at a dotted JSON path, or None when it is absent."""
    value = _resolve_json_path(payload, path)
    return None if value is _MISSING else value


def _read_response(response: Any) -> bytes:
    body = response.read(_MAX_BODY_BYTES + 1)
    if len(body) > _MAX_BODY_BYTES:
        raise ValueError("response body exceeds 1 MiB")
    return body


def _evaluate(check: Check, status: int, body: bytes) -> tuple[str, ...]:
    errors: list[str] = []
    if status != check.expected_status:
        errors.append(f"expected HTTP {check.expected_status}, got {status}")

    if not check.json_expectations:
        return tuple(errors)

    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        errors.append("response is not valid JSON")
        return tuple(errors)

    for path, expected in check.json_expectations:
        actual = _resolve_json_path(payload, path)
        if actual is _MISSING:
            errors.append(f"JSON path '{path}' is missing")
        elif type(actual) is not type(expected) or actual != expected:
            errors.append(f"JSON path '{path}': expected {expected!r}, got {actual!r}")
    return tuple(errors)


def check_endpoint(check: Check) -> CheckResult:
    started = time.perf_counter()
    status: int | None = None
    errors: tuple[str, ...]
    request = Request(
        check.url, headers={"User-Agent": "Traxy/0.1 (+https://github.com/traxy111/Traxy)"}
    )

    try:
        with _OPENER.open(request, timeout=check.timeout) as response:
            status = response.status
            body = _read_response(response)
        errors = _evaluate(check, status, body)
    except HTTPError as exc:
        status = exc.code
        try:
            body = _read_response(exc)
            errors = _evaluate(check, status, body)
        except (OSError, ValueError) as body_exc:
            errors = (f"request failed: {body_exc}",)
    except (OSError, TimeoutError, URLError, ValueError) as exc:
        errors = (f"request failed: {exc}",)

    duration_ms = max(0, round((time.perf_counter() - started) * 1000))
    return CheckResult(
        name=check.name,
        url=check.url,
        ok=not errors,
        status=status,
        duration_ms=duration_ms,
        errors=errors,
    )


def run_checks(checks: tuple[Check, ...]) -> tuple[CheckResult, ...]:
    return tuple(check_endpoint(check) for check in checks)
