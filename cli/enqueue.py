import typer
import json
import uuid
from datetime import datetime, timezone
from dateutil import parser
from core.storage import Database
from core.config import ConfigManager

app = typer.Typer(help="Manage job queue operations")
db = Database()


@app.command()
def enqueue(
    job_json: str = typer.Argument(..., help='Job JSON string, e.g. \'{"command": "echo Hello"}\'')
):
    """
    Enqueue a new job with optional scheduling, retries, and priority.
    Reads default max_retries and job_timeout from configuration.
    """
    config = ConfigManager().load()

    # -------------------------------
    # Parse job JSON
    # -------------------------------
    try:
        job_data = json.loads(job_json)
    except json.JSONDecodeError:
        typer.secho("Error: Invalid JSON format. Please provide valid JSON.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    job_id = job_data.get("id") or str(uuid.uuid4())
    command = job_data.get("command")

    if not command:
        typer.secho("Error: Missing required field 'command'.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # -------------------------------
    # Load configuration defaults
    # -------------------------------
    max_retries = int(job_data.get("max_retries", config.get("max_retries", 3)))
    priority = int(job_data.get("priority", 0))
    run_at = job_data.get("run_at")

    # -------------------------------
    # Parse run_at (convert to UTC)
    # -------------------------------
    if run_at:
        try:
            dt = parser.parse(run_at)
            if dt.tzinfo is None:
                dt = dt.astimezone()
            run_at_utc = dt.astimezone(timezone.utc)
            run_at_str = run_at_utc.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            typer.secho(
                f"Warning: Invalid 'run_at' format. Defaulting to now. ({e})",
                fg=typer.colors.YELLOW,
            )
            run_at_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    else:
        run_at_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # -------------------------------
    # Insert into database
    # -------------------------------
    try:
        db.add_job(job_id, command, max_retries, priority=priority, run_at=run_at_str)

        typer.secho("\nJob Enqueued Successfully", fg=typer.colors.GREEN, bold=True)
        typer.echo("-" * 50)
        typer.secho(f"ID        : {job_id}", fg=typer.colors.BRIGHT_WHITE)
        typer.secho(f"Command   : {command}", fg=typer.colors.BRIGHT_WHITE)
        typer.secho(f"Retries   : {max_retries}", fg=typer.colors.BRIGHT_WHITE)
        typer.secho(f"Priority  : {priority}", fg=typer.colors.BRIGHT_WHITE)
        typer.secho(f"Run At    : {run_at_str} UTC", fg=typer.colors.BRIGHT_WHITE)
        typer.echo("-" * 50)

    except Exception as e:
        typer.secho(f"Error: Failed to enqueue job ({e})", fg=typer.colors.RED)
        raise typer.Exit(code=1)
