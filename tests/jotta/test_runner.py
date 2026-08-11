import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QProcess

from jotta_gui.jotta.runner import Command, CommandResult, JottaRunner

pytestmark = pytest.mark.qt


def test_command_display() -> None:
    command = Command("status", ("status", "--json"))

    assert command.display == "jotta-cli status --json"


def test_command_result_prefers_stderr_for_failure() -> None:
    result = CommandResult(
        command=Command("sync_trigger", ("sync", "trigger")),
        exit_code=1,
        stdout="partial output",
        stderr="case collision",
    )

    assert result.succeeded is False
    assert result.error_message == "case collision"


def test_successful_process_completion_preserves_both_streams(qt_app, monkeypatch) -> None:
    runner = JottaRunner()
    runner._current = Command("status", ("status", "--json"))
    completed = []
    failed = []
    runner.completed.connect(completed.append)
    runner.failed.connect(failed.append)
    monkeypatch.setattr(runner, "_drain_process_output", lambda: ('{"ok": true}', "warning"))
    monkeypatch.setattr(runner, "_start_next", lambda: None)

    runner._process_finished(0, QProcess.ExitStatus.NormalExit)

    assert len(completed) == 1
    assert failed == []
    assert completed[0].stdout == '{"ok": true}'
    assert completed[0].stderr == "warning"
    assert completed[0].succeeded is True


def test_failed_process_completion_emits_structured_result(qt_app, monkeypatch) -> None:
    runner = JottaRunner()
    runner._current = Command("sync_start", ("sync", "start"))
    failed = []
    runner.failed.connect(failed.append)
    monkeypatch.setattr(runner, "_drain_process_output", lambda: ("stdout", "permission denied"))
    monkeypatch.setattr(runner, "_start_next", lambda: None)

    runner._process_finished(1, QProcess.ExitStatus.NormalExit)

    assert len(failed) == 1
    result = failed[0]
    assert result.command.name == "sync_start"
    assert result.exit_code == 1
    assert result.stdout == "stdout"
    assert result.stderr == "permission denied"
    assert result.error_message == "permission denied"


def test_failed_process_completion_has_exit_code_fallback(qt_app, monkeypatch) -> None:
    runner = JottaRunner()
    runner._current = Command("sync_stop", ("sync", "stop"))
    failed = []
    runner.failed.connect(failed.append)
    monkeypatch.setattr(runner, "_drain_process_output", lambda: ("", ""))
    monkeypatch.setattr(runner, "_start_next", lambda: None)

    runner._process_finished(7, QProcess.ExitStatus.NormalExit)

    assert failed[0].error_message == "jotta-cli exited with 7"
