"""CLI entry-point tests for ``fortios_mcp.server``."""

from __future__ import annotations

import pytest

from fortios_mcp import __version__
from fortios_mcp.server import _build_arg_parser, main
from fortios_mcp.utils.config import reset_settings_cache


def test_help_exits_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    """`fortios-mcp --help` must return help text and exit 0, not start the server."""
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "FortiOS MCP server" in out
    assert "--transport" in out
    assert "--check" in out


def test_version_prints_package_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert __version__ in out


def test_missing_credentials_exits_with_clean_message(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A missing FORTIOS_HOST/API_TOKEN must produce a short stderr message, not a traceback."""
    monkeypatch.delenv("FORTIOS_HOST", raising=False)
    monkeypatch.delenv("FORTIOS_API_TOKEN", raising=False)
    reset_settings_cache()
    try:
        with pytest.raises(SystemExit) as exc:
            main(["--check"])
        assert exc.value.code == 2
        err = capsys.readouterr().err
        assert "FORTIOS_HOST" in err
        assert "FORTIOS_API_TOKEN" in err
        assert "Traceback" not in err
    finally:
        monkeypatch.setenv("FORTIOS_HOST", "fake-fortigate.local")
        monkeypatch.setenv("FORTIOS_API_TOKEN", "test-token")
        reset_settings_cache()


def test_check_succeeds_with_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`--check` validates config then exits 0 without starting the transport."""
    monkeypatch.setenv("FORTIOS_HOST", "fake-fortigate.local")
    monkeypatch.setenv("FORTIOS_API_TOKEN", "test-token")
    monkeypatch.setenv("MCP_SERVER_MODE", "stdio")
    reset_settings_cache()
    try:
        assert main(["--check"]) == 0
    finally:
        reset_settings_cache()


def test_invalid_transport_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["--transport", "carrier-pigeon"])
    err = capsys.readouterr().err
    assert "carrier-pigeon" in err


def test_arg_parser_structure() -> None:
    """Sanity check the argparse surface for regressions."""
    parser = _build_arg_parser()
    actions = {a.dest for a in parser._actions}
    assert {"help", "version", "transport", "check"}.issubset(actions)


def test_keyboard_interrupt_exits_cleanly(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ctrl+C during `mcp.run` must produce a clean exit (code 130), not a traceback."""
    monkeypatch.setenv("FORTIOS_HOST", "fake-fortigate.local")
    monkeypatch.setenv("FORTIOS_API_TOKEN", "test-token")
    monkeypatch.setenv("MCP_SERVER_MODE", "stdio")
    reset_settings_cache()

    from fortios_mcp import server

    def _raise_keyboard_interrupt(*_args: object, **_kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(server.mcp, "run", _raise_keyboard_interrupt)
    try:
        assert main([]) == 130
        err = capsys.readouterr().err
        assert "Traceback" not in err
    finally:
        reset_settings_cache()
