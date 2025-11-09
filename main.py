import sys
import typer
import subprocess

# Import each command directly
from cli.enqueue import enqueue
from cli.list_jobs import list_jobs
from cli.worker import start as worker_start, stop as worker_stop
from cli.dlq import list_dlq, retry_job, purge_dlq
from cli.config_cli import set as config_set, get as config_get, show as config_show, reset as config_reset
from cli.status_cli import status

app = typer.Typer(
    help="QueueCTL - Background Job Queue System",
    add_completion=False,
)


# ======================================================
# Command Registration (Flat CLI)
# ======================================================

# --- Enqueue ---
app.command("enqueue")(enqueue)

# --- List Jobs ---
app.command("list")(list_jobs)

# --- Worker Management ---
app.command("worker-start")(worker_start)
app.command("worker-stop")(worker_stop)

# --- Dead Letter Queue ---
app.command("dlq-list")(list_dlq)
app.command("dlq-retry")(retry_job)
app.command("dlq-purge")(purge_dlq)

# --- Configuration Management ---
app.command("config-set")(config_set)
app.command("config-get")(config_get)
app.command("config-show")(config_show)
app.command("config-reset")(config_reset)

# --- System Status ---
app.command("status")(status)


# --- Dashboard Launch ---
@app.command("dashboard")
def dashboard():
    """
    Launch the QueueCTL web dashboard for real-time monitoring.
    """
    typer.echo(typer.style("Starting QueueCTL dashboard...", fg=typer.colors.CYAN))
    typer.echo(typer.style("URL: http://127.0.0.1:5000", fg=typer.colors.BLUE))
    subprocess.run([sys.executable, "web/dashboard.py"])


# ======================================================
# Entry Point
# ======================================================
if __name__ == "__main__":
    typer.echo(typer.style("QueueCTL CLI Initialized", fg=typer.colors.CYAN, bold=True))
    app()