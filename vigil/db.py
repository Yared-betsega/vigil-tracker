import sqlite3
from datetime import datetime
from pathlib import Path

from .models import Agent, Status

VIGIL_DIR = Path.home() / ".vigil"
DB_PATH   = VIGIL_DIR / "vigil.db"
LOGS_DIR  = VIGIL_DIR / "logs"


def _connect() -> sqlite3.Connection:
    VIGIL_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT UNIQUE NOT NULL,
            status      TEXT NOT NULL DEFAULT 'WAITING',
            pid         INTEGER,
            command     TEXT,
            task        TEXT,
            runtime     TEXT,
            workspace   TEXT,
            started_at  TEXT,
            finished_at TEXT,
            exit_code   INTEGER,
            log_file    TEXT,
            pane        TEXT
        )
    """)
    # add pane column to existing databases that predate this field
    cols = {r[1] for r in conn.execute("PRAGMA table_info(agents)")}
    if "pane" not in cols:
        conn.execute("ALTER TABLE agents ADD COLUMN pane TEXT")
    conn.commit()


def _row_to_agent(row: sqlite3.Row) -> Agent:
    def parse_dt(s: str | None) -> datetime | None:
        return datetime.fromisoformat(s) if s else None

    return Agent(
        id=row["id"],
        name=row["name"],
        status=Status(row["status"]),
        pid=row["pid"],
        command=row["command"],
        task=row["task"],
        runtime=row["runtime"],
        workspace=row["workspace"],
        started_at=parse_dt(row["started_at"]),
        finished_at=parse_dt(row["finished_at"]),
        exit_code=row["exit_code"],
        log_file=row["log_file"],
        pane=row["pane"],
    )


def list_agents() -> list[Agent]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM agents ORDER BY id").fetchall()
    return [_row_to_agent(r) for r in rows]


def get_agent(name: str) -> Agent | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM agents WHERE name = ?", (name,)).fetchone()
    return _row_to_agent(row) if row else None


def _dt_iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def insert_agent(agent: Agent) -> Agent:
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO agents
               (name, status, pid, command, task, runtime, workspace,
                started_at, finished_at, exit_code, log_file, pane)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (agent.name, agent.status.value, agent.pid, agent.command,
             agent.task, agent.runtime, agent.workspace,
             _dt_iso(agent.started_at), _dt_iso(agent.finished_at),
             agent.exit_code, agent.log_file, agent.pane),
        )
        conn.commit()
        agent.id = cur.lastrowid
    return agent


def update_agent(agent: Agent) -> None:
    with _connect() as conn:
        conn.execute(
            """UPDATE agents
               SET status=?, pid=?, command=?, task=?, runtime=?, workspace=?,
                   started_at=?, finished_at=?, exit_code=?, log_file=?, pane=?
               WHERE name=?""",
            (agent.status.value, agent.pid, agent.command, agent.task,
             agent.runtime, agent.workspace,
             _dt_iso(agent.started_at), _dt_iso(agent.finished_at),
             agent.exit_code, agent.log_file, agent.pane, agent.name),
        )
        conn.commit()


def delete_agent(name: str) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM agents WHERE name = ?", (name,))
        conn.commit()
    return cur.rowcount > 0
