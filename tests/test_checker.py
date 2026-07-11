from __future__ import annotations

from traxy.checker import check_endpoint, resolve_json_path, run_checks
from traxy.config import Check

from .conftest import local_server


def test_resolve_json_path_reads_nested_values() -> None:
    payload = {"service": {"version": "1.2.3"}}

    assert resolve_json_path(payload, "service.version") == "1.2.3"


def test_resolve_json_path_returns_missing_sentinel() -> None:
    payload = {"service": {"version": "1.2.3"}}

    assert resolve_json_path(payload, "service.commit") is None


def test_check_endpoint_passes_status_and_json_expectations() -> None:
    with local_server() as base_url:
        check = Check(
            name="health",
            url=f"{base_url}/health",
            expected_status=200,
            timeout=2,
            json_expectations=(("status", "ok"), ("service.version", "1.2.3")),
        )

        result = check_endpoint(check)

    assert result.ok is True
    assert result.status == 200
    assert result.errors == ()
    assert result.duration_ms >= 0


def test_check_endpoint_reports_http_and_json_failures() -> None:
    with local_server() as base_url:
        check = Check(
            name="missing",
            url=f"{base_url}/missing",
            expected_status=200,
            timeout=2,
            json_expectations=(("error", "different"),),
        )

        result = check_endpoint(check)

    assert result.ok is False
    assert result.status == 404
    assert "expected HTTP 200, got 404" in result.errors
    assert "JSON path 'error': expected 'different', got 'missing'" in result.errors


def test_check_endpoint_reports_non_json_response() -> None:
    with local_server() as base_url:
        check = Check(
            name="plain",
            url=f"{base_url}/plain",
            expected_status=200,
            timeout=2,
            json_expectations=(("status", "ok"),),
        )

        result = check_endpoint(check)

    assert result.ok is False
    assert result.errors == ("response is not valid JSON",)


def test_check_endpoint_reports_connection_error() -> None:
    check = Check(
        name="offline",
        url="http://127.0.0.1:1/health",
        expected_status=200,
        timeout=0.1,
        json_expectations=(),
    )

    result = check_endpoint(check)

    assert result.ok is False
    assert result.status is None
    assert result.errors[0].startswith("request failed:")


def test_run_checks_preserves_order() -> None:
    with local_server() as base_url:
        checks = (
            Check("first", f"{base_url}/health", 200, 2, ()),
            Check("second", f"{base_url}/missing", 404, 2, ()),
        )

        results = run_checks(checks)

    assert tuple(result.name for result in results) == ("first", "second")
    assert all(result.ok for result in results)


def test_json_expectations_are_type_strict() -> None:
    with local_server() as base_url:
        check = Check(
            name="strict",
            url=f"{base_url}/health",
            expected_status=200,
            timeout=2,
            json_expectations=(("count", True),),
        )

        result = check_endpoint(check)

    assert result.ok is False
    assert "expected True, got 1" in result.errors[0]


def test_redirects_are_checked_without_being_followed() -> None:
    with local_server() as base_url:
        check = Check(
            name="redirect",
            url=f"{base_url}/redirect",
            expected_status=302,
            timeout=2,
            json_expectations=(),
        )

        result = check_endpoint(check)

    assert result.ok is True
    assert result.status == 302
