from jotta_gui.jotta.runner import JottaRunner


def get_status(runner: JottaRunner) -> None:
    runner.run("status", ["status", "--json"])
