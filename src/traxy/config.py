from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_MAX_TIMEOUT_SECONDS = 300.0
_ROOT_KEYS = frozenset({"checks"})
_CHECK_KEYS = frozenset({"name", "url", "timeout", "expect"})
_EXPECT_KEYS = frozenset({"status", "json"})


class ConfigError(ValueError):
    """Raised when a Traxy configuration is invalid."""


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    url: str
    expected_status: int = 200
    timeout: float = 10.0
    json_expectations: tuple[tuple[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class Config:
    checks: tuple[Check, ...]


def _require_mapping(value: object, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{location} must be a JSON object")
    return value


def _reject_unknown_keys(value: dict[str, Any], allowed: frozenset[str], location: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ConfigError(f"{location} contains unknown key(s): {', '.join(unknown)}")


def _validate_url(value: object, index: int) -> str:
    location = f"checks[{index}].url"
    if not isinstance(value, str) or any(character.isspace() for character in value):
        raise ConfigError(f"{location} must be a valid http(s) URL")

    try:
        parsed = urlparse(value)
        port = parsed.port
    except ValueError as exc:
        raise ConfigError(f"{location} must be a valid http(s) URL") from exc

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or port is not None
        and not 1 <= port <= 65535
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise ConfigError(
            f"{location} must be a valid http(s) URL without credentials or fragments"
        )
    return value


def _parse_check(value: object, index: int) -> Check:
    item = _require_mapping(value, f"checks[{index}]")
    _reject_unknown_keys(item, _CHECK_KEYS, f"checks[{index}]")
    name = item.get("name")
    url = _validate_url(item.get("url"), index)
    timeout = item.get("timeout", 10.0)
    expect = _require_mapping(item.get("expect", {}), f"checks[{index}].expect")
    _reject_unknown_keys(expect, _EXPECT_KEYS, f"checks[{index}].expect")
    status = expect.get("status", 200)
    json_values = _require_mapping(expect.get("json", {}), f"checks[{index}].expect.json")

    if not isinstance(name, str) or not name.strip():
        raise ConfigError(f"checks[{index}].name must be a non-empty string")
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or not 0 < timeout <= _MAX_TIMEOUT_SECONDS
    ):
        raise ConfigError(
            f"checks[{index}].timeout must be greater than zero and at most "
            f"{_MAX_TIMEOUT_SECONDS:g} seconds"
        )
    if isinstance(status, bool) or not isinstance(status, int) or not 100 <= status <= 599:
        raise ConfigError(f"checks[{index}].expect.status must be an HTTP status code")

    expectations: list[tuple[str, Any]] = []
    for path, expected in json_values.items():
        if not isinstance(path, str) or not path or any(not part for part in path.split(".")):
            raise ConfigError(f"checks[{index}].expect.json keys must be non-empty dotted paths")
        expectations.append((path, expected))

    return Check(
        name=name.strip(),
        url=url,
        expected_status=status,
        timeout=float(timeout),
        json_expectations=tuple(expectations),
    )


def load_config(path: str | Path) -> Config:
    config_path = Path(path)
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise ConfigError(f"could not read configuration: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"configuration must be valid JSON: {exc.msg}") from exc

    root = _require_mapping(raw, "configuration")
    _reject_unknown_keys(root, _ROOT_KEYS, "configuration")
    checks = root.get("checks")
    if not isinstance(checks, list):
        raise ConfigError("configuration must contain a checks array")
    if not checks:
        raise ConfigError("configuration must contain at least one check")

    return Config(checks=tuple(_parse_check(item, index) for index, item in enumerate(checks)))
