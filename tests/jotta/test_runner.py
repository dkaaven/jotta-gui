
import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QProcess

from jotta_gui.jotta.runner import Command, JottaRunner

pytestmark = pytest.mark.qt


def test_successful_process_completion_emits_stdout(qt_app, monkeypatch) -> None:
    runner = JottaRunner()
    runner._current = Command("status", ("status", "--json"))
    completed = []
    errors = []
    runner.completed.connect(lambda name, output: completed.append((name, output)))
    runner.error.connect(lambda name, message: errors.append((name, message)))
    monkeypatch.setattr(runner, "_read_stdout", lambda: '{"ok": true}')
    monkeypatch.setattr(runner, "_read_stderr", lambda: "")
    monkeypatch.setattr(runner, "_start_next", lambda: None)

    runner._process_finished(0, QProcess.ExitStatus.NormalExit)

    assert completed == [("status", '{"ok": true}')]
    assert errors == []
    assert runner._current is None


def test_failed_process_completion_prefers_stderr(qt_app, monkeypatch) -> None:
    runner = JottaRunner()
    runner._current = Command("sync_start", ("sync", "start"))
    errors = []
    runner.error.connect(lambda name, message: errors.append((name, message)))
    monkeypatch.setattr(runner, "_read_stdout", lambda: "")
    monkeypatch.setattr(runner, "_read_stderr", lambda: "permission denied")
    monkeypatch.setattr(runner, "_start_next", lambda: None)

    runner._process_finished(1, QProcess.ExitStatus.NormalExit)

    assert errors == [("sync_start", "permission denied")]
    assert runner._current is None


def test_failed_process_completion_has_exit_code_fallback(qt_app, monkeypatch) -> None:
    runner = JottaRunner()
    runner._current = Command("sync_stop", ("sync", "stop"))
    errors = []
    runner.error.connect(lambda name, message: errors.append((name, message)))
    monkeypatch.setattr(runner, "_read_stdout", lambda: "")
    monkeypatch.setattr(runner, "_read_stderr", lambda: "")
    monkeypatch.setattr(runner, "_start_next", lambda: None)

    runner._process_finished(7, QProcess.ExitStatus.NormalExit)

    assert errors == [("sync_stop", "jotta-cli exited with 7")]
