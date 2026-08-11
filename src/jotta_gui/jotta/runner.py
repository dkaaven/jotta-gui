from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import logging

from PySide6.QtCore import QObject, QProcess, Signal

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Command:
    """One jotta-cli invocation queued for execution."""

    name: str
    arguments: tuple[str, ...]

    @property
    def display(self) -> str:
        return "jotta-cli " + " ".join(self.arguments)


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Structured result from a jotta-cli process.

    stdout and stderr are always retained, including on failures. This matters for
    long-running commands such as ``sync trigger`` where useful diagnostics may be
    split across both streams.
    """

    command: Command
    exit_code: int | None
    stdout: str
    stderr: str
    process_error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0 and self.process_error is None

    @property
    def error_message(self) -> str | None:
        if self.succeeded:
            return None
        if self.stderr:
            return self.stderr
        if self.process_error:
            return self.process_error
        if self.exit_code is not None:
            return f"jotta-cli exited with {self.exit_code}"
        return "jotta-cli failed"


class JottaRunner(QObject):
    """Sequential asynchronous runner for jotta-cli commands."""

    completed = Signal(object)  # CommandResult
    failed = Signal(object)  # CommandResult

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.process = QProcess(self)
        self._current: Command | None = None
        self._queue: deque[Command] = deque()
        self._process_error_message: str | None = None

        self.process.finished.connect(self._process_finished)
        self.process.errorOccurred.connect(self._process_error)

    def run(self, name: str, arguments: list[str] | tuple[str, ...]) -> None:
        self._queue.append(Command(name=name, arguments=tuple(arguments)))
        self._start_next()

    def _start_next(self) -> None:
        if self.process.state() != QProcess.ProcessState.NotRunning:
            return
        if self._current is not None or not self._queue:
            return

        self._current = self._queue.popleft()
        self._process_error_message = None
        logger.info("Running %s: %s", self._current.name, self._current.display)
        self.process.start("jotta-cli", list(self._current.arguments))

    def _process_finished(
        self,
        exit_code: int,
        exit_status: QProcess.ExitStatus,
    ) -> None:
        del exit_status

        command = self._take_current()
        if command is None:
            self._drain_process_output()
            self._start_next()
            return

        stdout, stderr = self._drain_process_output()
        result = CommandResult(
            command=command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            process_error=self._process_error_message,
        )
        self._process_error_message = None

        if result.succeeded:
            self.completed.emit(result)
        else:
            self.failed.emit(result)

        self._start_next()

    def _process_error(self, error: QProcess.ProcessError) -> None:
        message = self.process.errorString()

        # QProcess does not reliably emit finished() for FailedToStart.
        if error == QProcess.ProcessError.FailedToStart:
            command = self._take_current()
            stdout, stderr = self._drain_process_output()
            if command is not None:
                self.failed.emit(
                    CommandResult(
                        command=command,
                        exit_code=None,
                        stdout=stdout,
                        stderr=stderr,
                        process_error=message,
                    )
                )
            self._process_error_message = None
            self._start_next()
            return

        self._process_error_message = message

    def _take_current(self) -> Command | None:
        command = self._current
        self._current = None
        return command

    def _drain_process_output(self) -> tuple[str, str]:
        stdout = bytes(self.process.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        ).strip()
        stderr = bytes(self.process.readAllStandardError()).decode(
            "utf-8", errors="replace"
        ).strip()
        return stdout, stderr
