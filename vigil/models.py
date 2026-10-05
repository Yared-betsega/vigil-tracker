from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Status(str, Enum):
    WAITING  = "WAITING"
    RUNNING  = "RUNNING"
    FINISHED = "FINISHED"
    FAILED   = "FAILED"


@dataclass
class Agent:
    id: int
    name: str
    status: Status
    pid: int | None
    command: str | None
    task: str | None
    runtime: str | None
    workspace: str | None
    started_at: datetime | None
    finished_at: datetime | None
    exit_code: int | None
    log_file: str | None
    pane: str | None
