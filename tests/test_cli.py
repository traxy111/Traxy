from __future__ import annotations

import json
import subprocess
import sys

from traxy.cli import main

from .conftest import local_server


def _write_config(tmp_path, base_url: str, *, expected_status: int = 200):
    config_path = tmp_path / "traxy.json"
    config_path.write_text(
        json.dumps(
            {
                "checks": [
                    {
                        "name": "health",
                        "url": f"{base_url}/health",
                        "expect": {"status": expected_status, "json": {"status": "ok"}},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return config_path


def test_main_prints_human_summary(tmp_path, capsys) -> None:
    with local_server() as base_url:
        config_path = _write_config(tmp_path, base_url)
        exit_code = main(["run", str(config_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "PASS health" in output
    assert "1/1 checks passed" in output


def test_main_prints_machine_readable_json(tmp_path, capsys) -> None:
    with local_server() as base_url:
        config_path = _write_config(tmp_path, base_url)
        exit_code = main(["run", str(config_path), "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["summary"] == {"passed": 1, "total": 1}
    assert payload["results"][0]["name"] == "health"


def test_json_output_redacts_query_values(tmp_path, capsys) -> None:
    with local_server() as base_url:
        config_path = tmp_path / "traxy.json"
        config_path.write_text(
            json.dumps(
                {
                    "checks": [
                        {
                            "name": "health",
                            "url": f"{base_url}/health?token=secret",
                            "expect": {"status": 200, "json": {"status": "ok"}},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        exit_code = main(["run", str(config_path), "--format", "json"])

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert exit_code == 0
    assert "secret" not in output
    assert payload["results"][0]["url"].endswith("?REDACTED")


def test_main_returns_nonzero_for_failed_check(tmp_path, capsys) -> None:
    with local_server() as base_url:
        config_path = _write_config(tmp_path, base_url, expected_status=201)
        exit_code = main(["run", str(config_path)])

    assert exit_code == 1
    assert "FAIL health" in capsys.readouterr().out


def test_main_returns_usage_error_for_invalid_config(tmp_path, capsys) -> None:
    config_path = tmp_path / "bad.json"
    config_path.write_text("{}", encoding="utf-8")

    exit_code = main(["run", str(config_path)])

    assert exit_code == 2
    assert "configuration error:" in capsys.readouterr().err


def test_main_returns_usage_error_for_malformed_url(tmp_path, capsys) -> None:
    config_path = tmp_path / "bad-url.json"
    config_path.write_text(
        json.dumps({"checks": [{"name": "bad", "url": "https://example.com:invalid"}]}),
        encoding="utf-8",
    )

    exit_code = main(["run", str(config_path)])

    assert exit_code == 2
    assert "configuration error:" in capsys.readouterr().err


def test_python_module_e2e(tmp_path) -> None:
    with local_server() as base_url:
        config_path = _write_config(tmp_path, base_url)
        completed = subprocess.run(
            [sys.executable, "-m", "traxy", "run", str(config_path), "--format", "json"],
            check=False,
            capture_output=True,
            text=True,
        )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 0
    assert payload["ok"] is True
