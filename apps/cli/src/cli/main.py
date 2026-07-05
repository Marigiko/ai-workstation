"""AI Workstation CLI - Command-line interface for the AI Engineering Platform."""

import json
import sys

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cli.client import GatewayClient

app = typer.Typer(
    name="ai",
    help="AI Workstation CLI - Interact with the AI Engineering Platform",
    add_completion=False,
)
console = Console()


def get_client() -> GatewayClient:
    """Get gateway client instance."""
    return GatewayClient()


def handle_error(e: Exception):
    """Handle and display errors."""
    if hasattr(e, "response"):
        try:
            error_detail = e.response.json().get("detail", str(e))
        except Exception:
            error_detail = str(e)
    else:
        error_detail = str(e)
    console.print(f"[red]Error:[/red] {error_detail}")
    sys.exit(1)


@app.command()
def status():
    """Check gateway status."""
    try:
        client = get_client()
        client.health_check()
        console.print(Panel(f"[green]✓[/green] Gateway is healthy\nURL: {client.base_url}"))
    except Exception as e:
        handle_error(e)


@app.command()
def chat(
    message: str = typer.Argument(..., help="Message to send"),
    session: str | None = typer.Option(None, "--session", "-s", help="Session ID"),
):
    """Send a chat message."""
    try:
        client = get_client()
        messages = [{"role": "user", "content": message}]
        result = client.chat(messages, session_id=session)

        console.print(Panel(result["content"], title="Assistant", border_style="green"))

        if "usage" in result:
            usage = result["usage"]
            console.print(
                f"[dim]Tokens: {usage.get('total_tokens', 'N/A')} | "
                f"Latency: {result.get('latency_ms', 0):.2f}ms[/dim]"
            )
    except Exception as e:
        handle_error(e)


# Session commands
session_app = typer.Typer(help="Manage conversation sessions")
app.add_typer(session_app, name="session")


@session_app.command("create")
def session_create(title: str | None = typer.Option(None, "--title", "-t", help="Session title")):
    """Create a new session."""
    try:
        client = get_client()
        result = client.create_session(title)
        console.print(f"[green]✓[/green] Created session: {result['id']}")
        if title:
            console.print(f"  Title: {title}")
    except Exception as e:
        handle_error(e)


@session_app.command("list")
def session_list(limit: int = typer.Option(10, "--limit", "-l", help="Number of sessions")):
    """List recent sessions."""
    try:
        client = get_client()
        sessions = client.list_sessions(limit)

        if not sessions:
            console.print("[yellow]No sessions found[/yellow]")
            return

        table = Table(title="Sessions")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Created", style="dim")

        for session in sessions:
            table.add_row(
                session["id"][:8] + "...",
                session.get("title", "Untitled"),
                session["created_at"][:19],
            )

        console.print(table)
    except Exception as e:
        handle_error(e)


@session_app.command("show")
def session_show(session_id: str = typer.Argument(..., help="Session ID")):
    """Show session details."""
    try:
        client = get_client()
        session = client.get_session(session_id)

        console.print(Panel(f"Session: {session['id']}", title="Session Details"))
        console.print(f"Title: {session.get('title', 'Untitled')}")
        console.print(f"Created: {session['created_at']}")
        console.print(f"Turns: {len(session['turns'])}\n")

        for turn in session["turns"]:
            role = turn["role"].capitalize()
            content = turn["content"]
            if len(content) > 200:
                content = content[:200] + "..."
            console.print(f"[bold]{role}:[/bold] {content}")
    except Exception as e:
        handle_error(e)


@session_app.command("delete")
def session_delete(session_id: str = typer.Argument(..., help="Session ID")):
    """Delete a session."""
    try:
        client = get_client()
        client.delete_session(session_id)
        console.print(f"[green]✓[/green] Deleted session: {session_id}")
    except Exception as e:
        handle_error(e)


# Tools commands
tools_app = typer.Typer(help="Manage and execute tools")
app.add_typer(tools_app, name="tools")


@tools_app.command("list")
def tools_list():
    """List available tools."""
    try:
        client = get_client()
        result = client.list_tools()

        table = Table(title="Available Tools")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="green")

        for tool in result["tools"]:
            table.add_row(tool["name"], tool["description"])

        console.print(table)
    except Exception as e:
        handle_error(e)


@tools_app.command("exec")
def tools_exec(
    tool_name: str = typer.Argument(..., help="Tool name"),
    params: str = typer.Option("{}", "--params", "-p", help="JSON parameters"),
):
    """Execute a tool."""
    try:
        client = get_client()
        params_dict = json.loads(params)
        result = client.execute_tool(tool_name, params_dict)

        if result["success"]:
            output = json.dumps(result["output"], indent=2)
            console.print(Panel(output, title="Output", border_style="green"))
        else:
            console.print(f"[red]Error:[/red] {result['error']}")
    except json.JSONDecodeError:
        console.print("[red]Error:[/red] Invalid JSON in params")
        sys.exit(1)
    except Exception as e:
        handle_error(e)


# Skills commands
skills_app = typer.Typer(help="Manage and execute skills")
app.add_typer(skills_app, name="skills")


@skills_app.command("list")
def skills_list():
    """List available skills."""
    try:
        client = get_client()
        result = client.list_skills()

        table = Table(title="Available Skills")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Variables", style="yellow")

        for skill in result["skills"]:
            table.add_row(
                skill["name"],
                skill["description"],
                ", ".join(skill["variables"]),
            )

        console.print(table)
    except Exception as e:
        handle_error(e)


@skills_app.command("exec")
def skills_exec(
    skill_name: str = typer.Argument(..., help="Skill name"),
    variables: str = typer.Option("{}", "--vars", "-v", help="JSON variables"),
    context: str | None = typer.Option(None, "--context", "-c", help="Additional context"),
):
    """Execute a skill."""
    try:
        client = get_client()
        variables_dict = json.loads(variables)
        result = client.execute_skill(skill_name, variables_dict, context)

        if result["success"]:
            console.print(Panel(result["response"], title="Result", border_style="green"))
        else:
            console.print(f"[red]Error:[/red] {result['error']}")
    except json.JSONDecodeError:
        console.print("[red]Error:[/red] Invalid JSON in variables")
        sys.exit(1)
    except Exception as e:
        handle_error(e)


# Memory commands
memory_app = typer.Typer(help="Manage persistent memory")
app.add_typer(memory_app, name="memory")


@memory_app.command("remember")
def memory_remember(
    content: str = typer.Argument(..., help="Memory content"),
    scope: str = typer.Option("global", "--scope", "-s", help="Scope: global, project, session"),
    project_id: str | None = typer.Option(None, "--project", "-p", help="Project ID"),
    session_id: str | None = typer.Option(None, "--session", help="Session ID"),
):
    """Store a memory."""
    try:
        client = get_client()
        result = client.remember(content, scope, project_id, session_id)
        console.print(f"[green]✓[/green] Stored memory: {result['id']}")
    except Exception as e:
        handle_error(e)


@memory_app.command("recall")
def memory_recall(
    query: str = typer.Argument(..., help="Search query"),
    scope: str = typer.Option("global", "--scope", "-s", help="Scope: global, project, session"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    project_id: str | None = typer.Option(None, "--project", "-p", help="Project ID"),
    session_id: str | None = typer.Option(None, "--session", help="Session ID"),
):
    """Recall memories."""
    try:
        client = get_client()
        result = client.recall(query, scope, limit, project_id, session_id)

        if not result["memories"]:
            console.print("[yellow]No memories found[/yellow]")
            return

        for memory in result["memories"]:
            title = f"Memory ({memory['scope']})"
            console.print(Panel(memory["content"], title=title, border_style="blue"))
    except Exception as e:
        handle_error(e)


# Evaluation commands
eval_app = typer.Typer(help="Evaluate responses")
app.add_typer(eval_app, name="eval")


@eval_app.command("run")
def eval_run(
    query: str = typer.Option(..., "--query", "-q", help="Original query"),
    response: str = typer.Option(..., "--response", "-r", help="Response to evaluate"),
    metrics: str | None = typer.Option(None, "--metrics", "-m", help="Comma-separated metrics"),
):
    """Evaluate a response."""
    try:
        client = get_client()
        metrics_list = metrics.split(",") if metrics else None
        result = client.evaluate(query, response, metrics_list)

        table = Table(title="Evaluation Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Score", style="green")

        for eval_result in result["results"]:
            score = eval_result["score"]
            score_str = f"{score:.2f}"
            if score >= 0.8:
                score_str = f"[green]{score_str}[/green]"
            elif score >= 0.5:
                score_str = f"[yellow]{score_str}[/yellow]"
            else:
                score_str = f"[red]{score_str}[/red]"

            table.add_row(eval_result["metric"], score_str)

        console.print(table)
    except Exception as e:
        handle_error(e)


# Observability commands
@app.command()
def metrics():
    """Show observability metrics."""
    try:
        client = get_client()
        result = client.get_observability_summary()

        table = Table(title="Observability Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Traces", str(result["total_traces"]))
        table.add_row("Total Spans", str(result["total_spans"]))
        table.add_row("Total Metrics", str(result["total_metrics"]))
        table.add_row("Total Logs", str(result["total_logs"]))
        table.add_row("Error Rate", f"{result['error_rate']:.2%}")
        table.add_row("Avg Latency", f"{result['avg_latency_ms']:.2f}ms")
        table.add_row("P95 Latency", f"{result['p95_latency_ms']:.2f}ms")
        table.add_row("P99 Latency", f"{result['p99_latency_ms']:.2f}ms")

        console.print(table)
    except Exception as e:
        handle_error(e)


if __name__ == "__main__":
    app()
