from __future__ import annotations

import json

import pytest

from traxy.config import ConfigError, load_config


def test_load_config_returns_immutable_checks(tmp_path) -> None:
    path = tmp_path / "traxy.json"
    path.write_text(
        json.dumps(
            {
                "checks": [
                    {
                        "name": "API health",
                        "url": "https://example.com/health",
                        "expect": {
                            "status": 200,
                            "json": {"status": "ok", "service.version": "1.2.3"},
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    config = load_config(path)

    assert isinstance(config.checks, tuple)
    assert config.checks[0].name == "API health"
    assert config.checks[0].expected_status == 200
    assert config.checks[0].json_expectations == (
        ("status", "ok"),
        ("service.version", "1.2.3"),
    )


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({}, "checks"),
        ({"checks": []}, "at least one"),
        ({"checks": [{"name": "x", "url": "ftp://example.com"}]}, "http"),
        ({"checks": [{"name": "x", "url": "https://example.com", "timeout": 0}]}, "timeout"),
    ],
)
def test_load_config_rejects_invalid_input(tmp_path, payload, message) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigError, match=message):
        load_config(path)


def test_load_config_reports_invalid_json(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ConfigError, match="valid JSON"):
        load_config(path)


@pytest.mark.parametrize("timeout", [float("nan"), float("inf"), 301])
def test_load_config_rejects_unsafe_timeouts(tmp_path, timeout) -> None:
    path = tmp_path / "bad-timeout.json"
    path.write_text(
        json.dumps({"checks": [{"name": "x", "url": "https://example.com", "timeout": timeout}]}),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="timeout"):
        load_config(path)


def test_load_config_rejects_overflowed_json_timeout(tmp_path) -> None:
    path = tmp_path / "overflow-timeout.json"
    path.write_text(
        '{"checks":[{"name":"x","url":"https://example.com","timeout":1e309}]}',
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="timeout"):
        load_config(path)


@pytest.mark.parametrize(
    "url",
    [
        "https://[:::]/",
        "https://example.com:invalid/",
        "https://user:secret@example.com/",
        "https://exa mple.com/",
    ],
)
def test_load_config_rejects_malformed_or_sensitive_urls(tmp_path, url) -> None:
    path = tmp_path / "bad-url.json"
    path.write_text(json.dumps({"checks": [{"name": "x", "url": url}]}), encoding="utf-8")

    with pytest.raises(ConfigError, match="url"):
        load_config(path)


@pytest.mark.parametrize(
    "payload",
    [
        {"checks": [{"name": "x", "url": "https://example.com"}], "cheks": []},
        {"checks": [{"name": "x", "url": "https://example.com", "timout": 1}]},
        {
            "checks": [
                {
                    "name": "x",
                    "url": "https://example.com",
                    "expect": {"statsu": 500},
                }
            ]
        },
    ],
)
def test_load_config_rejects_unknown_keys(tmp_path, payload) -> None:
    path = tmp_path / "typo.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigError, match="unknown"):
        load_config(path)
