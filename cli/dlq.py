import typer
from core.storage import Database

app = typer.Typer(help="Manage Dead Letter Queue (DLQ) jobs")
db = Database()


# ----------------------------------------------------------------------
# LIST
# ----------------------------------------------------------------------
@app.command("list")
def list_dlq():
    """List all jobs currently in the Dead Letter Queue."""
    try:
        jobs = db.list_job_bystatus("dead")
        if not jobs:
            typer.echo(typer.style("DLQ is empty. No failed jobs found.", fg=typer.colors.YELLOW))
            raise typer.Exit(code=0)

        typer.echo(typer.style("Dead Letter Queue Jobs", fg=typer.colors.CYAN, bold=True))
        typer.echo("-" * 65)

        for job in jobs:
            typer.echo(
                f"ID         : {job['id']}\n"
                f"Command    : {job['command']}\n"
                f"Attempts   : {job['attempts']}/{job['max_retries']}\n"
                f"Created At : {job['created_at']}\n"
                f"Updated At : {job['updated_at']}\n"
                f"Status     : {job['status']}\n"
                + "-" * 65
            )

    except Exception as e:
        typer.echo(typer.style(f"Error listing DLQ jobs: {e}", fg=typer.colors.RED))
        raise typer.Exit(code=1)


# ----------------------------------------------------------------------
# RETRY
# ----------------------------------------------------------------------
@app.command("retry")
def retry_job(job_id: str):
    """Retry a specific DLQ job by moving it back to 'pending'."""
    try:
        job = db.get_job(job_id)
        if not job:
            typer.echo(typer.style(f"No job found with ID: {job_id}", fg=typer.colors.RED))
            raise typer.Exit(code=1)

        if job["status"] != "dead":
            typer.echo(
                typer.style(
                    f"Job {job_id} is not in DLQ (current status: {job['status']}).",
                    fg=typer.colors.YELLOW,
                )
            )
            raise typer.Exit(code=1)

        # Reset job for retry
        db.update_job_status(job_id, "pending")
        db.con.execute("UPDATE jobs SET attempts = 0 WHERE id=?", (job_id,))
        db.con.commit()

        typer.echo(
            typer.style(
                f"Job {job_id} moved back to 'pending' for retry.", fg=typer.colors.GREEN, bold=True
            )
        )
    except Exception as e:
        typer.echo(typer.style(f"Error retrying DLQ job: {e}", fg=typer.colors.RED))
        raise typer.Exit(code=1)


# ----------------------------------------------------------------------
# PURGE
# ----------------------------------------------------------------------
@app.command("purge")
def purge_dlq(confirm: bool = typer.Option(False, "--confirm", help="Confirm DLQ purge")):
    """Permanently delete all jobs from the DLQ (use with caution)."""
    if not confirm:
        typer.echo(
            typer.style(
                "Use '--confirm' to permanently purge all DLQ jobs.",
                fg=typer.colors.YELLOW,
            )
        )
        raise typer.Exit(code=1)

    try:
        with db.con:
            db.con.execute("DELETE FROM jobs WHERE status='dead';")
        typer.echo(
            typer.style("All DLQ jobs purged successfully.", fg=typer.colors.GREEN, bold=True)
        )
    except Exception as e:
        typer.echo(typer.style(f"Error purging DLQ: {e}", fg=typer.colors.RED))
        raise typer.Exit(code=1)
