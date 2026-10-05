import subprocess
from datetime import datetime

import psutil

from .db import update_agent
from .models import Agent, Status


def _tmux(args: list[str]) -> str:
    result = subprocess.run(["tmux"] + args, capture_output=True, text=True)
    return result.stdout.strip()


def tty_from_pane(pane: str) -> str | None:
    tty = _tmux(["display-message", "-t", pane, "-p", "#{pane_tty}"])
    return tty if tty else None


def capture_pane(pane: str, lines: int = 10) -> str:
    return _tmux(["capture-pane", "-t", pane, "-p", "-S", f"-{lines}"])


def pid_from_tty(tty: str) -> int | None:
    if not tty.startswith("/dev/"):
        tty = f"/dev/{tty}"
    candidates: list[psutil.Process] = []
    for proc in psutil.process_iter(["pid", "name", "terminal"]):
        try:
            if proc.info["terminal"] == tty:
                candidates.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if not candidates:
        return None
    for proc in candidates:
        if "claude" in (proc.info["name"] or "").lower():
            return proc.info["pid"]
    return candidates[0].info["pid"]


def attach(agent: Agent, pid: int) -> Agent:
    if not psutil.pid_exists(pid):
        raise ValueError(f"No process with PID {pid}")
    agent.pid        = pid
    agent.status     = Status.RUNNING
    agent.started_at = datetime.now()
    return agent


def poll(agent: Agent) -> Agent:
    if agent.status != Status.RUNNING or agent.pid is None:
        return agent
    if psutil.pid_exists(agent.pid):
        return agent
    agent.finished_at = datetime.now()
    agent.status      = Status.FINISHED
    update_agent(agent)
    return agent


def poll_all(agents: list[Agent]) -> list[Agent]:
    return [poll(a) for a in agents]
