from collections import deque
from dataclasses import dataclass
import logging

from PySide6.QtCore import QObject, QProcess, Signal

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Command:
    name: str
    arguments: tuple[str, ...]


class JottaRunner(QObject):
    completed = Signal(str, str)
    error = Signal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.process = QProcess(self)
        self._current: Command | None = None
        self._queue: deque[Command] = deque()
        self._process_error_message: str | None = None

        self.process.finished.connect(self._process_finished)
        self.process.errorOccurred.connect(self._process_error)

    def run(self, name: str, arguments: list[str]) -> None:
        self._queue.append(Command(name, tuple(arguments)))
        self._start_next()

    def _start_next(self) -> None:
        if self.process.state() != QProcess.ProcessState.NotRunning:
            return
        if self._current is not None or not self._queue:
            return

        self._current = self._queue.popleft()
        self._process_error_message = None
        logger.info(
            "Running %s: jotta-cli %s",
            self._current.name,
            " ".join(self._current.arguments),
        )
        self.process.start("jotta-cli", list(self._current.arguments))

    def _process_finished(
        self,
        exit_code: int,
        exit_status: QProcess.ExitStatus,
    ) -> None:
        del exit_status

        stdout = self._read_stdout()
        stderr = self._read_stderr()
        command = self._take_current()

        if command is None:
            self._start_next()
            return

        error_message = self._process_error_message
        self._process_error_message = None

        if exit_code != 0 or error_message:
            self.error.emit(
                command.name,
                stderr or error_message or f"jotta-cli exited with {exit_code}",
            )
        else:
            self.completed.emit(command.name, stdout)

        self._start_next()

    def _process_error(self, error: QProcess.ProcessError) -> None:
        message = self.process.errorString()

        # FailedToStart does not reliably produce a finished signal.
        if error == QProcess.ProcessError.FailedToStart:
            command = self._take_current()
            self._process_error_message = None
            if command is not None:
                self.error.emit(command.name, message)
            self._start_next()
            return

        self._process_error_message = message

    def _take_current(self) -> Command | None:
        command = self._current
        self._current = None
        return command

    def _read_stdout(self) -> str:
        return bytes(self.process.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        ).strip()

    def _read_stderr(self) -> str:
        return bytes(self.process.readAllStandardError()).decode(
            "utf-8", errors="replace"
        ).strip()
