import sys
import time
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv

load_dotenv(Path.home() / ".vigil" / ".env")
from rich.live import Live

from .db import delete_agent, get_agent, insert_agent, list_agents, update_agent
from .display import console, render_detail, render_detail_renderable, render_table
from .models import Agent, Status
from .tracker import attach as attach_pid, pid_from_tty, poll_all, tty_from_pane


@click.group()
def cli():
    """Vigil — observe your running agents and workflows."""


@cli.command()
@click.argument("name")
@click.argument("pid", type=int, required=False)
@click.option("--pane",      default=None, help="tmux pane to observe (e.g. 0, mywin:0, mywin:0.1)")
@click.option("--tty",       default=None, help="Terminal path (e.g. pts/3)")
@click.option("--task",      default=None, help="Task description")
@click.option("--runtime",   default=None, help="Runtime (e.g. Claude Code)")
@click.option("--workspace", default=None, help="Workspace path")
def attach(name, pid, pane, tty, task, runtime, workspace):
    """Attach to a process running in a tmux pane, tty, or by PID.

    \b
    Examples:
      vigil attach my-agent --pane 0
      vigil attach my-agent --pane mywin:0 --task "API refactor"
      vigil attach my-agent --tty pts/3
      vigil attach my-agent 18423
    """
    if get_agent(name):
        console.print(f"[red]Agent '{name}' already exists. Use `vigil rm {name}` first.[/red]")
        sys.exit(1)

    if pane:
        tty = tty_from_pane(pane)
        if not tty:
            console.print(f"[red]Could not find tty for pane '{pane}'. Is tmux running?[/red]")
            sys.exit(1)

    if tty:
        pid = pid_from_tty(tty)
        if pid is None:
            console.print(f"[red]No process found on tty '{tty}'.[/red]")
            sys.exit(1)
    elif pid is None:
        console.print("[red]Provide --pane, --tty, or a PID argument.[/red]")
        sys.exit(1)

    agent = Agent(id=0, name=name, status=Status.WAITING, pid=None, command=None,
                  task=task, runtime=runtime, workspace=workspace,
                  started_at=None, finished_at=None, exit_code=None, log_file=None,
                  pane=pane)
    try:
        agent = attach_pid(agent, pid)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    insert_agent(agent)
    info = f"PID {pid}"
    if pane:
        info += f", pane {pane}"
    console.print(f"[green]Attached[/green] {name} ({info})")


@cli.command()
@click.argument("name", required=False)
@click.option("--output", "-o", is_flag=True, help="Show raw pane output lines")
def status(name, output):
    """Show status of all agents, or detail for one agent."""
    if name:
        agent = get_agent(name)
        if not agent:
            console.print(f"[red]No agent named '{name}'.[/red]")
            sys.exit(1)
        poll_all([agent])
        agent = get_agent(name)
        render_detail(agent, show_output=output)
    else:
        agents = list_agents()
        agents = poll_all(agents)
        if not agents:
            console.print("[dim]No agents attached. Use `vigil attach`.[/dim]")
            return
        console.print(render_table(agents))


@cli.command()
@click.argument("name")
@click.option("--failed", is_flag=True, help="Mark as FAILED instead of FINISHED")
def done(name, failed):
    """Manually mark an agent finished or failed."""
    agent = get_agent(name)
    if not agent:
        console.print(f"[red]No agent named '{name}'.[/red]")
        sys.exit(1)
    agent.status      = Status.FAILED if failed else Status.FINISHED
    agent.finished_at = datetime.now()
    update_agent(agent)
    label = "FAILED" if failed else "FINISHED"
    color = "red" if failed else "green"
    console.print(f"Marked {name} as [{color}]{label}[/{color}]")


@cli.command()
@click.argument("name", required=False)
@click.option("--output", "-o", is_flag=True, help="Show raw pane output lines")
def watch(name, output):
    """Live-updating dashboard, or live pane output for one agent."""
    if name:
        with Live(refresh_per_second=1, screen=True) as live:
            try:
                while True:
                    agent = get_agent(name)
                    if not agent:
                        console.print(f"[red]No agent named '{name}'.[/red]")
                        sys.exit(1)
                    poll_all([agent])
                    agent = get_agent(name)
                    live.update(render_detail_renderable(agent, show_output=output))
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
    else:
        with Live(refresh_per_second=1, screen=False) as live:
            try:
                while True:
                    agents = list_agents()
                    agents = poll_all(agents)
                    live.update(render_table(agents))
                    time.sleep(1)
            except KeyboardInterrupt:
                pass


@cli.command()
@click.argument("name")
def rm(name):
    """Remove an agent record."""
    if not delete_agent(name):
        console.print(f"[red]No agent named '{name}'.[/red]")
        sys.exit(1)
    console.print(f"Removed {name}")
