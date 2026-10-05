from datetime import datetime

from rich import box
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import Agent, Status
from .summarizer import summarize
from .tracker import capture_pane

console = Console()

_ICONS: dict[Status, tuple[str, str]] = {
    Status.RUNNING:  ("●", "green"),
    Status.FINISHED: ("✓", "bright_green"),
    Status.FAILED:   ("✗", "red"),
    Status.WAITING:  ("⏸", "yellow"),
}


def _duration(agent: Agent) -> str:
    if agent.started_at is None:
        return "—"
    end  = agent.finished_at or datetime.now()
    secs = int((end - agent.started_at).total_seconds())
    if secs < 60:
        return f"{secs}s"
    m, s = divmod(secs, 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m"


def _started(agent: Agent) -> str:
    if agent.started_at is None:
        return "—"
    return agent.started_at.strftime("%I:%M %p").lstrip("0")


def _status_text(status: Status) -> Text:
    icon, color = _ICONS[status]
    return Text(f"{icon} {status.value}", style=color)


def render_table(agents: list[Agent]) -> Table:
    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold")
    table.add_column("AGENT", style="bold")
    table.add_column("STATUS")
    table.add_column("STARTED")
    table.add_column("DURATION")

    for agent in agents:
        table.add_row(
            agent.name,
            _status_text(agent.status),
            _started(agent),
            _duration(agent),
        )
    return table


def _detail_panel(agent: Agent, show_output: bool = False) -> Panel:
    icon, color = _ICONS[agent.status]

    lines = [
        f"[bold]Status:[/bold]       [{color}]{icon} {agent.status.value}[/{color}]",
        f"[bold]Started:[/bold]      {_started(agent)}",
        f"[bold]Duration:[/bold]     {_duration(agent)}",
    ]
    if agent.task:
        lines.append(f"[bold]Task:[/bold]         {agent.task}")
    if agent.runtime:
        lines.append(f"[bold]Runtime:[/bold]      {agent.runtime}")
    if agent.workspace:
        lines.append(f"[bold]Workspace:[/bold]    {agent.workspace}")
    if agent.pid:
        lines.append(f"[bold]PID:[/bold]          {agent.pid}")
    if agent.pane:
        lines.append(f"[bold]Pane:[/bold]         {agent.pane}")

    body = "\n".join(lines)

    if agent.pane:
        output = capture_pane(agent.pane, lines=20)
        if output:
            summary = summarize(agent.name, output)
            if summary:
                body += f"\n\n[bold cyan]What's happening:[/bold cyan] {escape(summary)}"
            if show_output:
                body += "\n\n[dim]Last output:[/dim]\n"
                body += "\n".join(f"  {escape(l)}" for l in output.splitlines())

    return Panel(body, title=f"[bold]{agent.name}[/bold]", expand=False)


def render_detail(agent: Agent, show_output: bool = False) -> None:
    console.print(_detail_panel(agent, show_output=show_output))


def render_detail_renderable(agent: Agent, show_output: bool = False) -> Panel:
    return _detail_panel(agent, show_output=show_output)
