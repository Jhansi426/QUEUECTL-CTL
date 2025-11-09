import typer
import time
import os
from core.worker_engine import WorkerManager
from core.config import ConfigManager

app = typer.Typer(help="Start or stop background worker threads for job processing.")


@app.command()
def start(
    count: int = typer.Option(None, "--count", "-c", help="Number of workers to start (overrides config)")
):
    """
    Start one or more worker threads to process pending jobs.
    Reads defaults from configuration unless overridden via CLI.
    """
    typer.echo(typer.style("\nStarting worker processes...", fg=typer.colors.CYAN, bold=True))

    # Load configuration
    config = ConfigManager()
    config_data = config.load()
    worker_count = count or config_data.get("worker_count", 1)
    backoff_base = config_data.get("backoff_base", 2)


    typer.echo(f"Configured Worker Count : {typer.style(worker_count, fg=typer.colors.GREEN)}")
    typer.echo(f"Backoff Base            : {typer.style(backoff_base, fg=typer.colors.GREEN)}")
    typer.echo("-" * 50)

    manager = WorkerManager(worker_count=worker_count, backoff_base=backoff_base)
    manager.start_workers()

    typer.echo(
        typer.style(
            f"{worker_count} worker(s) started. Press Ctrl+C to stop or run 'queuectl worker stop'.",
            fg=typer.colors.BLUE,
        )
    )

    try:
        while True:
            stop_file = getattr(WorkerManager, "STOP_SIGNAL_FILE", "stop_signal.json")

            # Stop requested internally
            if getattr(WorkerManager, "stop_flag", False):
                typer.echo(typer.style("Stop flag detected. Shutting down main process...", fg=typer.colors.YELLOW))
                break

            # Stop requested via stop signal file
            if os.path.exists(stop_file):
                typer.echo(typer.style("Stop signal file detected. Stopping all workers...", fg=typer.colors.YELLOW))
                break

            # No active workers remaining
            alive_threads = [t for t in getattr(WorkerManager, "workers", []) if t.is_alive()]
            if not alive_threads:
                typer.echo(typer.style("No active worker threads remain. Exiting process.", fg=typer.colors.BLUE))
                break

            time.sleep(0.5)

    except KeyboardInterrupt:
        typer.echo(typer.style("\nKeyboard interrupt detected. Requesting workers to stop...", fg=typer.colors.YELLOW))
        manager.stop_all()

    # Graceful shutdown
    typer.echo(typer.style("\nFinalizing worker shutdown...", fg=typer.colors.CYAN))
    wait_timeout = 10.0
    deadline = time.time() + wait_timeout
    while time.time() < deadline and any(t.is_alive() for t in getattr(WorkerManager, "workers", [])):
        time.sleep(0.2)

    # Cleanup stale files
    if os.path.exists(WorkerManager.STATUS_FILE):
        os.remove(WorkerManager.STATUS_FILE)

    typer.echo(typer.style("All workers stopped gracefully.", fg=typer.colors.GREEN, bold=True))
    typer.echo("-" * 50)


@app.command()
def stop():
    """
    Stop all active workers gracefully (can be run from another terminal).
    """
    typer.echo(typer.style("Sending stop signal to all workers...", fg=typer.colors.CYAN))
    WorkerManager.stop_all()
    typer.echo(typer.style("Stop signal sent successfully.", fg=typer.colors.GREEN, bold=True))
