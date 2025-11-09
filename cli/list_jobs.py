import typer
from core.storage import Database

app = typer.Typer(help="List and filter jobs by status")
db = Database()


@app.command()
def list_jobs(
    status: str = typer.Option(
        "all",
        "--status",
        "-s",
        help="Filter jobs by status (pending, processing, completed, failed, dead, or all)",
    )
):
    """List jobs by status or show all jobs."""
    try:
        # Handle 'all' explicitly
        if status.lower() == "all":
            query = "SELECT * FROM jobs ORDER BY created_at DESC"
            cur = db.con.cursor()
            cur.execute(query)
            jobs = cur.fetchall()
        else:
            jobs = db.list_job_bystatus(status)

        # Title
        typer.echo(typer.style(f"Job List — Status: {status.upper()}", fg=typer.colors.CYAN, bold=True))
        typer.echo("-" * 85)

        if not jobs:
            typer.echo(typer.style(f"No jobs found with status '{status}'.", fg=typer.colors.YELLOW))
            raise typer.Exit(code=0)

        # Table Header
        typer.echo(
            typer.style(f"{'ID':<36} {'STATUS':<12} {'PRIORITY':<8} {'ATTEMPTS':<9} {'CREATED_AT':<20}", bold=True)
        )
        typer.echo("-" * 85)

        # Job Rows
        for job in jobs:
            typer.echo(
                f"{job['id']:<36} "
                f"{job['status']:<12} "
                f"{job['priority']:<8} "
                f"{job['attempts']:<9} "
                f"{job['created_at']:<20}"
            )

        typer.echo("-" * 85)
        typer.echo(
            typer.style(f"Total Jobs Displayed: {len(jobs)}", fg=typer.colors.GREEN)
        )

    except Exception as e:
        typer.echo(typer.style(f"Failed to list jobs: {e}", fg=typer.colors.RED))
        raise typer.Exit(code=1)
